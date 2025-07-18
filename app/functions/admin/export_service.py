from typing import Any, List, Optional, AsyncGenerator
import pandas as pd
from app.utils.measure import measure_exe_time
import csv
import io
from fastapi.responses import StreamingResponse
from app.core.constants import Role


@measure_exe_time
async def export_transactions_to_csv(
        transactions: List[Any],
        name: Optional[str] = None,
) -> bytes:
    data = [transaction.dict() for transaction in transactions]

    df = pd.DataFrame(data)

    if name is not None:
        df.insert(0, "token_name", name)

    df = df.dropna(axis=1, how='all')

    csv_data = df.to_csv(index=False)

    return csv_data.encode("utf-8")


@measure_exe_time
async def export_transactions_csv_stream(
    transactions_gen: AsyncGenerator[Any, None],
    name: Optional[str] = None,
    role: Optional[str] = None,
    filename: str = "transactions.csv"
) -> StreamingResponse:
    async def csv_stream():
        output = io.StringIO()
        writer = csv.writer(output)

        exclude_fields = set()
        if role == Role.MERCHANT:
            exclude_fields.add("team_name")
        elif role == Role.AGENT:
            exclude_fields.add("merchant_payer_id")
        elif role == Role.TEAM:
            exclude_fields.add("team_name")
            exclude_fields.add("merchant_payer_id")

        header_written = False

        async for row in transactions_gen:
            row_dict = row.dict()
            if name is not None:
                row_dict.pop("token_name", None)
                row_dict = {"token_name": name, **row_dict}

            for field in exclude_fields:
                row_dict.pop(field, None)

            if not header_written:
                writer.writerow(row_dict.keys())
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
                header_written = True

            writer.writerow(row_dict.values())
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(csv_stream(), media_type="application/ms-excel", headers=headers)


