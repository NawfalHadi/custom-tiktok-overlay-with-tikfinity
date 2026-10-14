const payloads = {
    follow: {
      "event": "follow",
      "data": {
        "uniqueId": "naufaleon.id",
        "nickname": "Naufaleon",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/49f99b3d0a56cdd726829fcc96f5ee8d~tplv-tiktok-shrink:72:72.webp"
      }
    },
    gift: {
      "event": "gift",
      "data": {
        "uniqueId": "pementolan",
        "diamondCount": 1,
        "giftName": "Rose",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/3fe0241618b2a8e8a601af7ad28b7f72~tplv-tiktokx-cropcenter:100:100.webp"
      }
    },
    member: {
      "event": "member",
      "data": {
        "uniqueId": "mr..garuda1",
        "nickname": "MR. 𝖥𝖮𝖱𝖳𝖴𝖭𝖤𝖱",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/f86b3cfeab61a22f4cb39d2cc548b02d~tplv-tiktok-shrink:72:72.webp"
      }
    }
};

function sendFakeEvent(payloadKey) {
    const payload = payloads[payloadKey];
    console.log("Sending fake event to Flask SocketIO bridge:", payload);

    fetch('/api/fake-trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => console.log("Broadcasted successfully:", data))
    .catch(err => console.error("Error broadcasting fake event:", err));
}