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
            const emoji = emojiEl.textContent;
            const postId = post.dataset.postId;
            fetch("/react", {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                body: `post_id=${postId}&emoji=${encodeURIComponent(emoji)}`
            })
            
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let existing = reactionsDiv.querySelector(`[data-emoji="${emoji}"]`);
                    if (!existing) {
                        let span = document.createElement("span");
                        span.dataset.emoji = emoji;
                        span.textContent = `${emoji} × ${data.count}`;
                        reactionsDiv.appendChild(span);
                    } else {
                        existing.textContent = `${emoji} × ${data.count}`;
                    }
                    location.reload(); 
                }
            });
            picker.classList.add("hidden");
        });
    });
});