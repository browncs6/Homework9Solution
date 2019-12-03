const MESSAGE_TYPE = {
  CONNECT: 0,
  MSG: 1,
  HISTORY: 2,
  LIST: 3,
  SENT: 4,
  ERROR: 5
};

const make_message = (type, payload) => {
  return JSON.stringify({ type: type, payload: payload });
};

let $username_field;
let $password_field;
let $login_button;

const login_attempt = () => {
	$.post(
		"http://127.0.0.1:7000/chat",
		make_message(MESSAGE_TYPE.CONNECT, 
			{
				username: $username_field.val(),
      			password: $password_field.val()
      		}),
		(resp) => {
			switch (resp.type) {
				case MESSAGE_TYPE.CONNECT:
					token = resp.payload.token
					window.location = "./chat.html?token=" + token
					break;
				case MESSAGE_TYPE.ERROR:
					console.log(resp.payload.msg)
					break;
				default:
					console.log(resp)
					break;
			}
		}
	);
}

$(document).ready(() => {
  $username_field = $("#username");
  $password_field = $("#password");
  $login_button = $("#loginButton");
  $login_button.click(login_attempt);
  console.log("set up")
});

