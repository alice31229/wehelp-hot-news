let counter = 1;

// fetch /api/article/{id}
function ProcessImgs(imgs) { // pyscript

    let img_box = document.querySelector('.img_box');
    let dot_box = document.querySelector('.dot_box');

    imgs.forEach((img, ind) => {

        let newImg = document.createElement('img');
        newImg.setAttribute('src', img);
        newImg.setAttribute('class', 'article_imgs fade');
        img_box.appendChild(newImg);


        // image slide
        // make selection btn and arrows according to the imgs amounts
        let dot = document.createElement('img');
        dot.setAttribute('src', '/static/photo_icon/circle.png');
        dot.setAttribute('class', 'dot');
        dot.setAttribute('id', ind);
        dot_box.appendChild(dot);

        // Set the first image and dot as active
        if (ind === 0) {
            newImg.classList.add('active');
            dot.setAttribute('src', '/static/photo_icon/circle current.png');
        }

    });

};


// use re to extract the article id
function extractNumberFromPath(pathname) {
    
    const match = pathname.match(/\/(\d+)$/);
    
    return match ? match[1] : null;
}


async function LoadArticle() {

    try {
        const postResponse = await fetch(`/api${window.location.pathname}`);
        const postData = await postResponse.text();
        const article_result = JSON.parse(postData);
        let info = article_result.data;

        // details for correspondiing article info
        let title = document.querySelector('.title');
        let category_at_forum = document.querySelector('.category_at_forum');
        let content = document.querySelector('.content');
        let resource = document.querySelector('.resource');
        let date = document.querySelector('.date');
        let reference = document.querySelector('.article_link');
        let overview = document.querySelector('.overview');
        
        if (!article_result.error) {
            title.textContent = info.title;
            
            // handle null forum information
            if (info.forum != null) {
                category_at_forum.textContent = `${info.forum} from ${info.resource}`;
            } else {
                category_at_forum.textContent = `${info.forum}`;
            }
            
            overview.textContent = info.overview;
            content.textContent = info.content;
            resource.textContent = info.resource;
            date.textContent = info.date;
            reference.setAttribute('href', info.url);
            let img_lst = [info.wordcloud, info.network];
            ProcessImgs(img_lst);

        } else {
            window.location.href = '/';
        }
    } catch (e) {
        console.error('Error fetching article:', e);
    }

}


function minusSlides(n) {
    let slides = document.querySelectorAll('.article_imgs');
    let dots = document.querySelectorAll('.dot');

    if (n > slides.length) {
        counter = 1;
    }
    if (n < 1) {
        counter = slides.length;
    }

    slides.forEach(slide => slide.style.display = "none");
    dots.forEach(dot => dot.setAttribute('src', '/static/photo_icon/circle.png'));

    if (slides[counter - 1] && dots[counter - 1]) {
        slides[counter - 1].style.display = 'block';
        dots[counter - 1].setAttribute('src', '/static/photo_icon/circle current.png');
    }

}


function plusSlides(n) {
    let slides = document.querySelectorAll('.article_imgs');
    let dots = document.querySelectorAll('.dot');

    if (n > slides.length) {
        counter = 1;
    }
    if (n < 1) {
        counter = slides.length;
    }

    slides.forEach(slide => slide.style.display = "none");
    dots.forEach(dot => dot.setAttribute('src', '/static/photo_icon/circle.png'));

    if (slides[counter - 1] && dots[counter - 1]) {
        slides[counter - 1].style.display = 'block';
        dots[counter - 1].setAttribute('src', '/static/photo_icon/circle current.png');
    }
}



document.addEventListener("DOMContentLoaded", function () {

    // Because LoadArticle is asynchronous, use a callback or promise
    // so the myslide.length can get the accurate rendered article img
    LoadArticle().then(() => {

        // sign-in pop up
        let signIn = document.querySelector('.pop-background-color-sign-in');
        let closeSignIn = document.querySelector('.close-pop-sign-in');
        let signInEnroll = document.getElementById('signInEnroll');
        signInEnroll.addEventListener('click', function() {
            if (signInEnroll.textContent === '登入/註冊'){
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.add('show');
                signIn.style.display = 'flex';
            }
        })
        closeSignIn.addEventListener('click', function(){
            const fadeElement = document.getElementById('fade-sign-in');
            fadeElement.classList.remove('show');
            clearInputValue();
            adjustHeightAll();
            signIn.style.display = 'none';
        })
        signIn.addEventListener('click', function(event) {
            if (event.target === signIn) {

                // if error message shows -> hide
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.remove('show');
                let errorShow = document.querySelector('.error-message-sign-in');
                errorShow.style.display = 'none';
                clearInputValue();
                adjustHeightAll();
                signIn.style.display = 'none';

            }
        })

        // check log in or not
        async function checkLogin() {
            const token = localStorage.getItem("authToken");
            try {
                const response = await fetch('/api/user/auth', {
                    method: "GET",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });
    
                if (response.ok) {
                    const data = await response.json();
                    let memberInfoLS = JSON.parse(localStorage.getItem("memberInfo"));
                    if (data.data!=null && !memberInfoLS) {
                        // User is authenticated
                        let signInEnroll = document.querySelector('#signInEnroll');
                        signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;
    
                        document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                    } else if (memberInfoLS) {
                        let signInEnroll = document.querySelector('#signInEnroll');
                        signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${memberInfoLS.selfie}" alt="signInIcon">會員專區`;
    
                        document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                    }
                    // if (data.data!=null) {
                    //     // User is authenticated
                    //     let signInEnroll = document.querySelector('#signInEnroll');
                    //     signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;
                        
                    //     document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                    // } 
                    else {
                        // Token is invalid or expired
                        localStorage.removeItem("authToken");
                        localStorage.removeItem("memberInfo");
                        showSignInButton();
                    }
                } else {
                    throw new Error("Failed to verify token");
                }

            } catch (error) {
                console.error("Error verifying token:", error);
                localStorage.removeItem("authToken");
                localStorage.removeItem("memberInfo");
                showSignInButton();
            }
    
            if (!token) { 
                showSignInButton();
            }
        }

        function showSignInButton() {
            let signInEnroll = document.querySelector('#signInEnroll');
            signInEnroll.innerHTML = '<img class="signIn-enroll-icon" src="/static/photo_icon/log-in.png" alt="signInIcon">登入/註冊';
        }

        // log out -> remove localStorage token
        // function logout() {
        //     localStorage.removeItem("authToken");
        //     checkLogin();  // update log out -> log-in/enroll
        // }

        // go to member page
        function GoMemberPage() {
            window.location.assign('/member');
        }

        checkLogin();

        // enroll sign-in switch
        let enroll = document.querySelector('.pop-background-color-enroll');
        let enrollSwitch = document.querySelector('.enroll-dialog');
        let backSignIn = document.querySelector('.sign-in-dialog');
        let closeEnroll = document.querySelector('.close-pop-enroll');


        enrollSwitch.addEventListener('click', function() {
            signIn.style.display = 'none';
            enroll.style.display = 'flex';
            clearInputValue();
            adjustHeightAll();
        })
        backSignIn.addEventListener('click', function() {
            enroll.style.display = 'none';
            signIn.style.display = 'flex';
            clearInputValue();
            adjustHeightAll();
        })
        closeEnroll.addEventListener('click', function() {
            const fadeElement = document.getElementById('fade-sign-in');
            fadeElement.classList.remove('show');
            enroll.style.display = 'none';
            clearInputValue();
            adjustHeightAll();
        })
        enroll.addEventListener('click', function(event) {
            if (event.target === enroll) {
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.remove('show');
                let enrollShow = document.querySelector('.message-enroll');
                enrollShow.style.display = 'none';
                enroll.style.display = 'none';
            }
        })

        // sign in token await
        const loginForm = document.getElementById("signin"); // 要用form而不是button
        loginForm.addEventListener('submit', async function(event) {
            
            event.preventDefault();

            let username = document.querySelector('#usernameID');
            let password = document.querySelector('#passwordID');

            try {
                const response = await fetch('/api/user/auth', {
                    method: "PUT",
                    body: JSON.stringify({
                        username: username.value,
                        password: password.value
                    }),
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                let tokenJson = await response.json();
                
                //if (!response.ok) {
                if (!response.ok || !tokenJson.token) {
                    //let errorMessage = decodeURIComponent(tokenJson.message);
                    let errorMessage = tokenJson.message;

                    let adjustHeight = document.querySelector('.pop-up-sign-in');
                    adjustHeight.style.height = '310px';

                    let errorMsgShow = document.querySelector('.error-message-sign-in'); 
                    errorMsgShow.style.display = 'block';
                    errorMsgShow.textContent = errorMessage;

                    // Add event listener to hide error message on clicking other parts of the sign-in dialog
                    adjustHeight.addEventListener('click', function() {
                        errorMsgShow.style.display = 'none';
                        adjustHeightAll();
                    }, { once: true });

                } else {
                    let token = tokenJson.token;

                    // save token in localStorage
                    localStorage.setItem("authToken", token);

                    // close sign in dilalog
                    const fadeElement = document.getElementById('fade-sign-in');
                    fadeElement.classList.remove('show');
                    let closeSignIn = document.querySelector('.pop-background-color-sign-in');
                    closeSignIn.style.display = 'none';

                    // 登入/註冊 -> 會員專區
                    let signInEnroll = document.getElementById('signInEnroll');
                    signInEnroll.textContent = '會員專區';

                    //const token = localStorage.getItem("authToken");
                    try {
                        const response = await fetch('/api/user/auth', {
                            method: "GET",
                            headers: {
                                "Authorization": `Bearer ${token}`,
                                "Content-Type": "application/json"
                            }
                        });
            
                        if (response.ok) {
                            const data = await response.json();
                            
                            let memberInfoLS = JSON.parse(localStorage.getItem("memberInfo"));
                            if (data.data!=null && !memberInfoLS) {
                                // User is authenticated
                                let signInEnroll = document.querySelector('#signInEnroll');
                                signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;
            
                                document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                            } else if (memberInfoLS) {
                                let signInEnroll = document.querySelector('#signInEnroll');
                                signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${memberInfoLS.selfie}" alt="signInIcon">會員專區`;
            
                                document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                            }
                            // if (data.data) {
                            //     // User is authenticated
                            //     let signInEnroll = document.querySelector('#signInEnroll');
                            //     signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;
                            //     document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                            // } 
                            else {
                                // Token is invalid or expired
                                localStorage.removeItem("authToken");
                                localStorage.removeItem("memberInfo");
                                showSignInButton();
                            }
                        } else {
                            throw new Error("Failed to verify token");
                        }

                    } catch (error) {
                        console.error("Error verifying token:", error);
                        localStorage.removeItem("authToken");
                        localStorage.removeItem("memberInfo");
                        showSignInButton();
                    }
            
                    if (!token) { 
                        showSignInButton();
                    }

                    // 確保token已存入localStorage後才重整頁面
                    Promise.resolve().then(() => {
                    
                        location.reload();

                    });

                }


            } catch (error) {
                console.error("Login failed:", error);
            }

        })


        // register await
        let registerSubmit = document.querySelector('#enroll');
        registerSubmit.addEventListener('submit', async function(event) {
            
            event.preventDefault();

            let username = document.querySelector('#usernameID-enroll');
            let name = document.querySelector('#nameID-enroll');
            let email = document.querySelector('#emailID-enroll');
            let password = document.querySelector('#passwordID-enroll');

            try {

                const response = await fetch('/api/user', {
                    method: "POST",
                    body: JSON.stringify({
                        username: username.value,
                        name: name.value,
                        email: email.value,
                        password: password.value
                    }),
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                let result = await response.json();
                let enrollResult = document.querySelector('.message-enroll');

                if (result.ok){

                    let adjustHeight = document.querySelector('.pop-up-enroll');
                    adjustHeight.style.height = '422px';

                    enrollResult.style.display = 'block';
                    enrollResult.style.color = 'green';
                    enrollResult.textContent = '註冊成功，請登入系統';

                    clearInputValue();

                    // Add event listener to hide error message on clicking other parts of the sign-in dialog
                    adjustHeight.addEventListener('click', function() {
                        enrollResult.style.display = 'none';
                        adjustHeightAll();
                    }, { once: true });

                }else {

                    let adjustHeight = document.querySelector('.pop-up-enroll');
                    adjustHeight.style.height = '422px';

                    enrollResult.style.display = 'block';
                    enrollResult.style.color = 'rgb(137, 28, 28)';
                    enrollResult.textContent = result.message;

                    // Add event listener to hide error message on clicking other parts of the sign-in dialog
                    adjustHeight.addEventListener('click', function() {
                        enrollResult.style.display = 'none';
                        adjustHeightAll();
                    }, { once: true });

                }

            }catch (error){
                console.error("Register failed:", error);
            }

        })

        // clear any input value
        function clearInputValue() {
            document.querySelector('#usernameID').value = '';
            document.querySelector('#usernameID-enroll').value = '';
            document.querySelector('#passwordID').value = '';
            document.querySelector('#passwordID-enroll').value = '';
            document.querySelector('#nameID-enroll').value = '';
            document.querySelector('#emailID-enroll').value = '';
        }
        // adjust sign in / enroll result height
        function adjustHeightAll() {
            document.querySelector('.pop-up-sign-in').style.height = '275px';
            document.querySelector('.pop-up-enroll').style.height = '392px';
        }


        // img slider arrow
        // if only one img -> no cursor at arrows;  
        let leftArrow = document.querySelector('.arrow_btn_left');
        let rightArrow = document.querySelector('.arrow_btn_right');
        let myslide = document.querySelectorAll('.article_imgs');
        let dots = document.querySelector('.dot_box');
        let dot = document.querySelector('.dot');

        // if only one article img
        if (myslide.length == 1) {
            leftArrow.classList.add('disabled');
            rightArrow.classList.add('disabled');
            dots.classList.add('disabled');
            dot.classList.add('disabled');
        }

        leftArrow.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent triggering any other click events
            counter = counter - 1;
            minusSlides(counter);
        });

        rightArrow.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent triggering any other click events
            counter = counter + 1;
            plusSlides(counter);
        });

        // click dot then show the img, change counter index to the target dot
        //let dots = document.querySelector('.dot_box');
        dots.addEventListener('click', async (event) => {
            if (event.target.classList.contains('dot')) {

                let dotsDot = document.querySelectorAll('.dot');

                dotsDot.forEach(dot => dot.setAttribute('src', '/static/photo_icon/circle.png'));
                event.target.setAttribute('src', '/static/photo_icon/circle current.png');

                counter = parseInt(event.target.id) + 1;

                let slides = document.querySelectorAll('.imgs_article');
                slides.forEach(slide => slide.style.display = "none");
                slides[counter - 1].style.display = 'block';

            }

        })

        plusSlides(counter);

    }).catch(error => {
        console.error('Error loading article:', error);
    });

    // 回首頁
    let home = document.querySelector('.home');
    home.addEventListener('click', () => {
        window.location.href = '/';
    })

    // click 觀看收藏文章
    // 是 -> POST: /api/collections -> collection page
    // 否 -> sign in dialog 
    let CollectBtn = document.querySelector('.start_collect');
    CollectBtn.addEventListener('click', async (event) => {

        event.preventDefault();
        

        // 查看是否登入 
        try {
            const token = localStorage.getItem("authToken");
            const getResponse = await fetch('/api/user/auth', {
                method: 'GET',
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
    
            let result = await getResponse.json();
    
            if (!result.data) { // not log in
    
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.add('show');
                let signIn = document.querySelector('.pop-background-color-sign-in');
                signIn.style.display = 'flex';

            } else { // log in

                let articleId = extractNumberFromPath(window.location.pathname);
                articleId = parseInt(articleId);
                articleId = articleId.toString();

                let memberId = result.data.id;
                memberId = memberId.toString();

                const collectNew = await fetch('/api/collect', {
                    method: 'POST',
                    body: JSON.stringify({
                        articleId: articleId,
                        memberId: memberId
                    }),
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                })

                let collectResult = await collectNew.json();

                if (collectResult.ok) {

                    window.location.assign('/member');

                } else {

                    console.log(`${collectResult.message}`);

                }

            }
        } catch(e) {

            console.log('check sign in error');

        }


    })

    // 看收藏文章
    let readCollections = document.querySelector('#readCollections');
    readCollections.addEventListener('click', async event => {

        event.preventDefault();

        // 登入驗證
        try {
            const token = localStorage.getItem("authToken");
            const getResponse = await fetch('/api/user/auth', {
                method: 'GET',
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
    
            let result = await getResponse.json();
    
            if (!result.data) { // not log in
    
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.add('show');
                let signIn = document.querySelector('.pop-background-color-sign-in');
                signIn.style.display = 'flex';

            } else { // log in

                // fix '/article/collect' issue
                let currentUrl = window.location.href;
                let newUrl = currentUrl.replace(/\/article\/.*/, '/member');
                window.location.assign(newUrl);

            }

        } catch (e) {
            console.log(e);
        }

        // 已收藏過的文章 收藏按鈕可以反灰

    })

});


