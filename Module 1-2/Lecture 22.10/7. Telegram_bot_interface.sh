#!/bin/bash

get_me() {
    curl -s "$url/getMe" | jq
}

get_updates() {
    curl -s "${url}/getUpdates" | jq
}

send_message() {
    curl -s -X POST "${url}/sendMessage" -d chat_id="$1" -d text="$2" | jq
}

read -rp "Enter your bot id token: " token

url="https://api.telegram.org/bot${token}"

select op in "Get me" "Get updates" "Send message" "Exit from script"; do
    case $op in
    "Get me")
        get_me;;
    "Get updates")
        get_updates;;
    "Send message")
        read -rp "Write chat id: " id_chat
        read -rp "Write your message: " message
        
        send_message "$id_chat" "$message";;
    "Exit from script")
        break;;
    *)
        echo "Unknown operation";;
    esac
done

echo "Successful completion of the script."
