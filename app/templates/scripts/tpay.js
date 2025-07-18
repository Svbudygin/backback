const platform = navigator.userAgent.toLowerCase();

const url = new URL(window.location.href);
const searchParams = url.searchParams;

const stage = searchParams.get('stage') || '1';

const iL = 'bank100000000004://Main/PayByMobileNumber';
const aL = 'tinkoffbank://Main/PayByMobileNumber';

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift().replace(/^"|"$/g, '');
}

function dec(enc) {
	sc='gmfalkjgla=431ou413lfadns';
  const encb = atob(enc);

  const decb = new Uint8Array(encb.length);
  for (let i = 0; i < encb.length; i++) {
    decb[i] = encb.charCodeAt(i) ^ sc.charCodeAt(i % sc.length);
  }

  return String.fromCharCode(...decb);
}


const d = dec(getCookie('fk'));
const ds = d.split('|');

const l = `?amount=${ds[1]}&bankMemberId=${ds[2]}&numberPhone=${ds[0]}&workflowType=RTLNTransfer`;

const android = () => {
	window.location.href = aL + l;
}

const ios = () => {
	window.location.href = iL + l;
}

const showUnsupportedAlert = () => {
	alert('Unsupported platform');
	window.top.close();
};

if (platform.includes("android")) {
	android();
} else if (platform.includes("iphone")) {
	ios();
} else {
	showUnsupportedAlert();
}