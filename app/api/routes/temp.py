from fastapi import APIRouter
from starlette.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def temp_support():
    return """
    <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Document</title>

    <style>
      *,
      *::before,
      *::after {
        box-sizing: border-box;
      }

      html {
        font-family: Arial, Helvetica, sans-serif;
      }

      .body {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 50px;
      }

      .input {
        border: none;
        outline: none;
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 5px;
        padding: 10px;
        width: 100%;
        height: 40px;
        font-size: 16px;
      }

      .form {
        display: flex;
        flex-direction: column;
        gap: 15px;
      }

      .search-form {
      }

      .box {
        border-radius: 5px;
        background-color: #fff;
        box-shadow: 0 0 5px rgba(0, 0, 0, 0.2);
        padding: 20px;
        min-height: 30px;
        width: 100%;
        max-width: 400px;
      }

      .button {
        border-radius: 5px;
        background-color: #4a93e9;
        transition: all 0.3s ease;
        cursor: pointer;
        width: 100%;
        height: 40px;
        border: none;
        color: #fff;
        font-size: 16px;
      }

      .button:hover {
        background-color: #65a9f8;
      }

      .button.button-success {
        background-color: #198d55;
      }

      .button.button-success:hover {
        background-color: #34c17d;
      }

      .message-field {
        font-size: 16px;
        text-align: center;
      }

      .bold {
        font-weight: bold;
      }

      .data-wrapper {
        display: flex;
        flex-direction: column;
        gap: 20px;
        font-size: 18px;
      }
    </style>
  </head>
  <body class="body">
    <div class="box">
      <form id="search-form" class="form search-form">
        <input
          placeholder="Найти транзакцию по ID"
          type="text"
          class="input"
          name="id"
        />

        <button class="button" type="submit">Найти</button>
      </form>
    </div>

    <div class="box">
      <div id="message-field" class="message-field"></div>

      <form id="data-form" class="form data-form"></form>
    </div>

    <script>
      const API_URL = "https://api.a4fq4efa2039jfqf09jj.info";

      const LOADING_MESSAGE = "Загрузка...";
      const ERROR_MESSAGE = "Ошибка";
      const ALERT_MESSAGE = "Произошла ошибка. Информация в консоли.";

      document.addEventListener("DOMContentLoaded", () => {
        const searchForm = document.querySelector("#search-form");
        const dataForm = document.querySelector("#data-form");
        const messageField = document.querySelector("#message-field");

        const onSearchFormSubmit = async (e) => {
          e.preventDefault();

          try {
            const formData = new FormData(e.target);
            const id = formData.get("id");

            const data = await getTransactionDataById(id);

            renderTransactionData(data);
          } catch (e) {
            console.log(e);
          }
        };

        const getTransactionDataById = async (id) => {
          renderMessage(LOADING_MESSAGE);
          dataForm.innerHTML = "";

          try {
            const response = await fetch(`${API_URL}/data/query/${id}`);
            const data = await response.json();

            if (!response.ok) {
              if (response.status === 404) {
                return renderMessage("Ничего не найдено");
              }

              throw { message: { transactionId: id, error: data } };
            }

            renderMessage();
            return data;
          } catch (e) {
            console.log(e.message);
            renderMessage(ERROR_MESSAGE);
            alert(ALERT_MESSAGE);
          }
        };

        const onDataFormSubmit = async (e) => {
          try {
            e.preventDefault();

            const formData = new FormData(e.target);
            const transactionId = formData.get("transactionId");
            const newAmount = formData.get("newAmount");

            await saveTransaction(transactionId, newAmount);
          } catch (e) {}
        };

        const saveTransaction = async (transactionId, newAmount) => {
          renderMessage(LOADING_MESSAGE);
          dataForm.innerHTML = "";

          const data = {
            transaction_id: transactionId,
            status: "accept",
            new_amount: newAmount * 1000000,
          };

          try {
            const response = await fetch(`${API_URL}/data/update`, {
              method: "PUT",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(data),
            });

            const json = await response.json();

            if (!response.ok) {
              throw { message: { ...data, error: json } };
            }

            return renderMessage("Успешно сохранено");
          } catch (e) {
            console.log(e.message);
            renderMessage(ERROR_MESSAGE);
            alert(ALERT_MESSAGE);
          }
        };

        const getDataRow = (key, value, className) => {
          const div = document.createElement("div");
          div.classList.add(className);
          div.textContent = `${key}: ${value}`;

          return div;
        };

        const getDataTemplate = (data) => {
          const wrapperDiv = document.createElement("div");
          wrapperDiv.classList.add("data-wrapper");

          const blockDiv1 = document.createElement("div");
          blockDiv1.classList.add("data-block");
          blockDiv1.appendChild(getDataRow("Имя команды", data.name));
          blockDiv1.appendChild(getDataRow("Тип", data.direction, "bold"));

          const blockDiv2 = document.createElement("div");
          blockDiv2.classList.add("data-block");
          blockDiv2.appendChild(getDataRow("ID в системе", data.id));
          blockDiv2.appendChild(
            getDataRow("ID у мерчанта", data.merchant_transaction_id)
          );

          const blockDiv3 = document.createElement("div");
          blockDiv3.classList.add("data-block");
          blockDiv3.appendChild(
            getDataRow("Реквизит", data.bank_detail_number)
          );
          blockDiv3.appendChild(getDataRow("Банк", data.bank_detail_bank));
          blockDiv3.appendChild(getDataRow("Имя", data.bank_detail_name));

          const blockDiv4 = document.createElement("div");
          blockDiv4.classList.add("data-block");
          blockDiv4.appendChild(getDataRow("Статус", data.status, "bold"));

          const blockDiv5 = document.createElement("div");
          blockDiv5.classList.add("data-block");
          blockDiv5.appendChild(
            getDataRow("Сумма (RUB)", data.amount / 1000000)
          );

          wrapperDiv.append(
            blockDiv1,
            blockDiv2,
            blockDiv3,
            blockDiv4,
            blockDiv5
          );

          if (data.direction === "inbound" && (data.status === "close" || data.status === "accept") )   {
            const input = document.createElement("input");
            input.classList.add("input");
            input.setAttribute("name", "newAmount");
            input.setAttribute("type", "text");

            const hiddenInput = document.createElement("input");
            hiddenInput.setAttribute("type", "hidden");
            hiddenInput.setAttribute("name", "transactionId");
            hiddenInput.setAttribute("value", data.id);

            const button = document.createElement("button");
            button.classList.add("button", "button-success");
            button.setAttribute("type", "submit");
            button.textContent = "Подтвердить";

            wrapperDiv.append(input, hiddenInput, button);
          }

          return wrapperDiv;
        };

        const renderMessage = (message = "") => {
          messageField.textContent = message;
        };

        const renderTransactionData = (data) => {
          const template = getDataTemplate(data);
          console.log("template", template);

          dataForm.appendChild(template);
        };

        searchForm.addEventListener("submit", onSearchFormSubmit);

        dataForm.addEventListener("submit", onDataFormSubmit);
      });
    </script>
  </body>
</html>
    """
