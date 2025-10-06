const replyInput = document.getElementById("reply_to_input");
const replyInfo = document.getElementById("reply_info");
const cancelBtn = document.getElementById("cancel_reply");

document.querySelectorAll(".reply-btn").forEach(btn => {
    btn.addEventListener("click", e => {
        e.preventDefault();
        const id = btn.dataset.replyTo;
        replyInput.value = id;
        replyInfo.innerHTML = "返信中 → <a href='#note-" + id + "'>投稿#" + id + " <\a> ";
        cancelBtn.style.display = "inline";
        window.scrollTo({top: 0, behavior:"smooth"});
    });
});

cancelBtn.addEventListener("click", () => {
    replyInput.value = "";
    replyInfo.innerHTML = "";
    cancelBtn.style.display = "none";
});


document.querySelectorAll(".note").forEach(post => {
    const addBtn = post.querySelector(".add-reaction");
    const picker = post.querySelector(".emoji-picker");
    const reactionsDiv = post.querySelector(".reactions");

    addBtn.addEventListener("click", (e) => {
        e.preventDefault();
        picker.classList.toggle("hidden");
    });

    picker.querySelectorAll(".emoji").forEach(emojiEl => {
        emojiEl.addEventListener("click", () => {
            const emojiId = emojiEl.dataset.id;
            const postId = post.dataset.postId;
            fetch("/react", {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: `post_id=${postId}&emoji_id=${emojiId}`
            })
            
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
            picker.classList.add("hidden");
        });
    });
});