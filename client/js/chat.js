const MESSAGE_TYPE = {
  CONNECT: 0,
  MSG: 1,
  HISTORY: 2,
  LIST: 3,
  SENT: 4,
  ERROR: 5
};

function getUrlToken() {
  let l = window.location.href.replace(/.*\?token=([a-zA-Z0-9]{24})$/, '$1')
  if (l.length === 24) {
    return l
  }
  return ""
}

const setup_websocket = (token) => {
  conn = new WebSocket("ws://127.0.0.1:7000/websocket?token=" + token);
  conn.onerror = err => {
    console.log("Connection error:", err);
  };
  conn.onmessage = msg => {
    console.log("Receiving:", msg.data);
    handle_message(JSON.parse(msg.data));
  };
};

const make_message = (type, payload) => {
  return JSON.stringify({ type: type, payload: payload, token: getUrlToken()});
};

let post_endpoint = "http://127.0.0.1:7000/chat"

let $online_ul;
let $offline_ul;
let $msg_field;
let $send_button;
let $history_div;

let curr_conversation = "";

const handle_message = msg => {
  payload = msg.payload;
  console.log("type:", msg.type);
  switch (msg.type) {
    case MESSAGE_TYPE.MSG:
      handle_msg(payload.from, payload.msg);
      break;
    case MESSAGE_TYPE.LIST:
      onlineUsers = msg.payload.online;
      offlineUsers = msg.payload.offline;
      handle_list(onlineUsers, offlineUsers)
      break;
    case MESSAGE_TYPE.ERROR:
      console.error(msg.payload.msg)
      break;
    default:
      console.error("invalid message type");
  }
};

const handle_msg = (from, msg) => {
  console.log(`Received message from ${from}`)
}

const handle_list = (onlineUsers, offlineUsers) => {
  $online_ul.empty();
  for (let i = 0; i < onlineUsers.length; i++) {
    $online_ul.append(`<li onclick='set_current_conversation(\"${onlineUsers[i]}\")'>${onlineUsers[i]}</li>`);
  }
  $offline_ul.empty();
  for (let i = 0; i < offlineUsers.length; i++) {
    $offline_ul.append(`<li onclick='set_current_conversation(\"${offlineUsers[i]}\")'>${offlineUsers[i]}</li>`);
  }
}

const set_current_conversation = (user) => {
  $history_div.empty();
  $.post(post_endpoint,
    make_message(MESSAGE_TYPE.HISTORY, 
      {
        user: user,
      }),
    (resp) => {
      switch (resp.type) {
        case MESSAGE_TYPE.HISTORY:
          curr_conversation = user;
          message_list = resp.payload
          for (let i = 0; i < message_list.length; i++) {
            $history_div.append(`<li>${message_list[i].from} -> ${message_list[i].to}: ${message_list[i].msg}</li>`);
          }
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

const send_message = () => {
  if (curr_conversation.length > 0) {
    $.post(post_endpoint,
      make_message(MESSAGE_TYPE.MSG, 
        {
          to: curr_conversation,
          msg: $msg_field.val()
        }),
      (resp) => {
        switch (resp.type) {
          case MESSAGE_TYPE.SENT:
            $msg_field.empty();
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
}

$(document).ready(() => {
  token = getUrlToken()
  if (token.length > 0) {
    setup_websocket(token);
  } else {
    console.error("Could not set up websocket: token not found in URL.")
  }
  $online_ul = $("#onlineList");
  $offline_ul = $("#offlineList");
  $msg_field = $("#msg");
  $send_button = $("#sendButton");
  $send_button.click(send_message)
  $history_div = $("#conversationDiv");
});
