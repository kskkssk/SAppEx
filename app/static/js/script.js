document.addEventListener('DOMContentLoaded', function() {

     var path = window.location.href;
     $('.d-flex.ms-auto a').each(function() {
          if (this.href === path) {
          $(this).addClass('active').siblings().removeClass('active');
        }
     });

    closeButton = document.getElementById("close-btn");
    if (closeButton) {
        closeButton.addEventListener("click", function(event) {
        event.preventDefault();
        window.location.href = '/';
    });
    }
    searchBtn = document.getElementById("search-btn");
    if (searchBtn) {
        searchBtn.addEventListener("click", function(event) {
            event.preventDefault();

            const form = document.querySelector("form");
            const formData = new FormData(form);

            term = document.getElementById("term").value;
            maxResults = document.getElementById("max_results").value;

            if (term === '' || maxResults === '') {
                event.preventDefault();
                alert('Проверьте заполнение обязательных полей: запрос, количество результатов');
                window.location.href = '/';
            }
            fetch("/search", {
                method: "POST",
                body: formData,
                headers: {
            "Accept": "application/json",
                },
            })
            .then(response => {
                if (!response.ok) {
                    alert("Ошибка при отправке запроса");
                    window.location.href = '/';
                }
                return response.json();
            })
            .then(data => {
                console.log("Ответ от сервера:", data);
            })
            .catch(error => {
                console.error("Ошибка:", error);
            });

            let socket = new WebSocket("ws://127.0.0.1:8080/ws");

            socket.onopen = function(e) {
                console.log("[open] Соединение установлено");
            };

            socket.onmessage = function(event) {
                let data = JSON.parse(event.data);

                if (data && data.percent !== undefined && data.step) {
                    var percent = data.percent;
                    var status = data.step;

                    const progressBar = document.getElementById("progress");
                    if (progressBar) {
                        progressBar.style.width = percent + '%';
                    };

                    const progressStatus = document.getElementById("progress-status");
                    if (progressStatus) {
                        progressStatus.innerText = status;
                    };

                    if (data.error) {
                        alert("Ошибка: " + data.error);
                    };
                };
                if (data && data.percent === 100 && data.step === "Готово!") {
                    window.location.href = '/results';
                }
            };

            socket.onclose = function(event) {
                if (event.wasClean) {
                    console.log('[close] Соединение закрыто чисто, код=${event.code} причина=${event.reason}');
                } else {
                    console.log('[close] Соединение прервано');
                }
            };

            socket.onerror = function(error) {
                alert('[error] Ошибка: ${error.message}');
            };
        });
    }
});
