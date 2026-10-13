// Full JSON payloads captured from TikFinity / TikTok Live events
const payloads = {
    giftRose: {
      "event": "gift",
      "data": {
        "giftId": 5655,
        "repeatCount": 1,
        "repeatEnd": true,
        "groupId": "1791686162982",
        "userIdentity": {
          "isGiftGiverOfAnchor": true,
          "isMutualFollowingWithAnchor": true,
          "isFollowerOfAnchor": true
        },
        "userId": "7498777180740060176",
        "secUid": "MS4wLjABAAAAW5SwWSpbjyH-8Fy0v5n50OzXum1YyXNj-YeB4mIE2I9C4PXAj5uzfPaDpc6oKYqp",
        "uniqueId": "pementolan",
        "nickname": "Komunitas Pementolan Duniawi",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/3fe0241618b2a8e8a601af7ad28b7f72~tplv-tiktokx-cropcenter:100:100.webp",
        "diamondCount": 1,
        "giftName": "Rose",
        "giftPictureUrl": "https://p19-webcast.tiktokcdn.com/img/maliva/webcast-va/eba3a9bb85c33e017f3648eaf88d7189~tplv-obj.png"
      }
    },
    giftHighValue: {
      "event": "gift",
      "data": {
        "giftId": 7934,
        "repeatCount": 25,
        "userIdentity": {
          "isGiftGiverOfAnchor": true,
          "isMutualFollowingWithAnchor": true,
          "isFollowerOfAnchor": true
        },
        "userId": "7498777180740060176",
        "secUid": "MS4wLjABAAAAW5SwWSpbjyH-8Fy0v5n50OzXum1YyXNj-YeB4mIE2I9C4PXAj5uzfPaDpc6oKYqp",
        "uniqueId": "pementolan",
        "nickname": "Komunitas Pementolan Duniawi",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/3fe0241618b2a8e8a601af7ad28b7f72~tplv-tiktokx-cropcenter:100:100.webp",
        "diamondCount": 10,
        "giftName": "Galaxy / Special Gift",
        "giftPictureUrl": "https://p19-webcast.tiktokcdn.com/img/alisg/webcast-sg/resource/composed.b326356a360b67b367c5cae58fe337b1.png~tplv-resize:258:258.webp"
      }
    },
    follow: {
      "event": "follow",
      "data": {
        "followerCount": 989,
        "userId": "6579166160360128513",
        "secUid": "MS4wLjABAAAAgapF8aSiK4IoqQ5azrK7a4TrOAMyVr0IkOthGGlKQPctIi81-JVSGXZ3DAMYjl5R",
        "uniqueId": "naufaleon.id",
        "nickname": "Naufaleon",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/49f99b3d0a56cdd726829fcc96f5ee8d~tplv-tiktok-shrink:72:72.webp",
        "username": "naufaleon.id"
      }
    },
    join: {
      "event": "member",
      "data": {
        "actionId": 1,
        "userId": "7484474769820632081",
        "secUid": "MS4wLjABAAAAb40E9Cf51JaAHXGxRE7k09S2_09Fve2xKfMZ3GreYZp2tf70wvOyiIOlggdTQvqY",
        "uniqueId": "mr..garuda1",
        "nickname": "MR. 𝖥𝖮𝖱𝖳𝖴𝖭𝖤𝖱",
        "profilePictureUrl": "https://p16-common-sign.tiktokcdn.com/tos-alisg-avt-0068/f86b3cfeab61a22f4cb39d2cc548b02d~tplv-tiktok-shrink:72:72.webp"
      }
    }
};

// Generic function to post any fake payload to your server endpoint
function sendFakeWebhook(endpoint, payloadKey) {
    const payload = payloads[payloadKey];
    console.log(`Hitting endpoint [${endpoint}] with payload:`, payload);

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => console.log("Success:", data))
    .catch(err => console.error("Error posting fake payload:", err));
}