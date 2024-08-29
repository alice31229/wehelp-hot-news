function eventsDomTree(events) {
    const more_articles = document.querySelector('.load_articles');

    events.forEach(event => {
        // Create picture div
        const picture = document.createElement('div');
        picture.setAttribute('class', 'picture');

        // img
        const eventP = document.createElement('img');
        eventP.src = event.wordcloud;
        eventP.setAttribute('class', 'content');

        const articleName = document.createElement('div');
        articleName.setAttribute('class', 'title');
        articleName.textContent = event.title;

        picture.appendChild(eventP);
        //picture.appendChild(articleName);

        // Create word div
        const word = document.createElement('div');
        word.setAttribute('class', 'word');

        // attraction_mrt
        const articleForum = document.createElement('div');
        articleForum.setAttribute('class', 'article_forum');
        articleForum.textContent = event.forum;

        // attraction_category
        const articleResource = document.createElement('div');
        articleResource.setAttribute('class', 'article_resource');
        articleResource.textContent = event.resource;

        word.appendChild(articleForum);
        word.appendChild(articleResource);

        // Unite picture and word into picture_word
        const picture_word = document.createElement('div');
        picture_word.setAttribute('class', 'picture_word');
        picture_word.setAttribute('id', event.id);

        // Append picture and word divs to the load_articles div
        picture_word.appendChild(picture);
        picture_word.appendChild(articleName);
        picture_word.appendChild(word);

        more_articles.appendChild(picture_word);
    });
}

// append hot keywords to recommend users
function AppendHotKwd() {

}

// add article category to the filter options -> call /api/forums
function AddArticleCategory() {

}

// provide overall and each resource category distribution
function ProvideCategoryDist() {

} 

let nextPage = 0;
let isLoading = false;

async function addArticle(page = 0) {
    if (isLoading) return; // Prevent multiple fetch requests
    isLoading = true;

    let clr = document.querySelector('.noArticle');
    clr.style.display = 'none';
    let footer = document.querySelector('.copyRight');
    footer.style.display = 'none';
    footer.style.position = '';

    let loading = document.querySelector('#loading');
    loading.style.display = 'block';

    try {
        const postResponse = await fetch(`/api/articles?page=${page}`);
        const postData = await postResponse.text();
        const article_result = JSON.parse(postData);
        let infos = article_result.data;

        eventsDomTree(infos);

        // Judge last page or not then show footer
        if (article_result.nextPage == null) {
            nextPage = 0;
            loading.style.display = 'none';
            footer.style.display = 'flex';
        } else {
            nextPage = article_result.nextPage;
        }
    } catch (e) {
        console.error('Error fetching articles:', e);
    } finally {
        isLoading = false;
    }
}

async function addKwdArticle(page = 0, keyword) {
    if (isLoading) return; // Prevent multiple fetch requests
    isLoading = true;

    let clr = document.querySelector('.noArticle');
    clr.style.display = 'none';
    let footer = document.querySelector('.copyRight');
    footer.style.display = 'none';
    footer.style.position = '';

    let loading = document.querySelector('#loading');
    loading.style.display = 'block';

    try {
        const postResponse = await fetch(`/api/articles?page=${page}&keyword=${keyword}`);
        const postData = await postResponse.text();
        const article_result = JSON.parse(postData);
        let infos = article_result.data;

        if (article_result.error) {
            check();
        } else {
            eventsDomTree(infos);
        }

        // Judge last page or not then add footer
        if (article_result.nextPage == null) {
            nextPage = 0;
            loading.style.display = 'none';
            footer.style.display = 'flex';
        } else {
            nextPage = article_result.nextPage;
        }
    } catch (e) {
        console.error('Error fetching keyword articles:', e);
    } finally {
        isLoading = false;
    }
}

function check() {
    let no_article = document.querySelector('.noArticle');
    no_article.style.display = 'flex';
    let footerFixed = document.querySelector('.copyRight');
    footerFixed.style.position = 'fixed';
}

async function addForum() {
    try {
        const postResponse = await fetch('/api/forums');
        const postData = await postResponse.text();
        const forum_result = JSON.parse(postData);
        let infos = forum_result.data;

        let appendHere = document.querySelector('.forums');

        infos.forEach(f => {
            const newForumDiv = document.createElement('div');
            newForumDiv.textContent = f;
            newForumDiv.className = 'forum';

            appendHere.appendChild(newForumDiv);
        });
    } catch (e) {
        console.error('Error fetching Forums:', e);
    }
}

// loading before the data fetch back from db and backend
window.addEventListener("load", () => {
    const loader = document.querySelector(".loader");
    loader.classList.add('loader--hidden');
    // setTimeout(() => {
    //     loader.classList.add('loader--hidden');
    // }, 1500);
});

document.addEventListener("DOMContentLoaded", function () {
    
    // const memberInfo = JSON.parse(localStorage.getItem("memberInfo"));
    // if (memberInfo) {



    // } else{

    addForum();
    addArticle();
    checkLogin();

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

            const fadeElement = document.getElementById('fade-sign-in');
            fadeElement.classList.remove('show');
            // if error message shows -> hide
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
                if (data.data!=null && !memberInfoLS) { // 登出後 token 已更新 會以更新的資訊為主
                    // User is authenticated
                    let signInEnroll = document.querySelector('#signInEnroll');
                    signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;

                    document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                } else if (memberInfoLS) { // 尚未登出 但剛改完 以更改的會員資訊為主
                    let signInEnroll = document.querySelector('#signInEnroll');
                    signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${memberInfoLS.selfie}" alt="signInIcon">會員專區`;

                    document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
                }
                // if (data.data!=null) {
                //     // User is authenticated
                //     let signInEnroll = document.querySelector('#signInEnroll');
                //     signInEnroll.innerHTML = `<img class="signIn-enroll-icon" src="${data.data.selfie}" alt="signInIcon">會員專區`;
                    
                //     document.querySelector('#signInEnroll').addEventListener("click", GoMemberPage);
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

    function GoMemberPage() {
        window.location.assign('/member');
    }


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
            
            if (!response.ok || !tokenJson.token) {
                
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

                // close sign in dialog
                let closeSignIn = document.querySelector('.pop-background-color-sign-in');
                const fadeElement = document.getElementById('fade-sign-in');
                fadeElement.classList.remove('show');
                closeSignIn.style.display = 'none';

                // 登入/註冊 -> 會員專區
                let signInEnroll = document.getElementById('signInEnroll');
                signInEnroll.textContent = '會員專區';

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
                        } else {
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
            //alert("登入失敗，請確認使用者名稱與密碼是否正確、已註冊");
            console.error("Login failed:", error);
        }

    })


    // register await
    let registerSubmit = document.querySelector('#enroll');
    registerSubmit.addEventListener('submit', async function(event) {
        
        event.preventDefault();

        let username = document.querySelector('#usernameID-enroll');
        let password = document.querySelector('#passwordID-enroll');
        let name = document.querySelector('#nameID-enroll');
        let email = document.querySelector('#emailID-enroll');

        try {

            const response = await fetch('/api/user', {
                method: "POST",
                body: JSON.stringify({
                    username: username.value,
                    password: password.value,
                    name: name.value,
                    email: email.value
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

    // clear any popup input value
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

    // infinite scroll observer settings
    let observer;
    const observerOptions = {
        root: null,
        rootMargin: '100px',
        threshold: 0.1
    };

    const createObserver = (callback) => {
        if (observer) observer.disconnect(); // avoid observers interfering each other
        observer = new IntersectionObserver(callback, observerOptions);
        const loadingElement = document.querySelector('#loading');
        observer.observe(loadingElement);
    };

    const observerCallback = entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !isLoading) {
                if (nextPage) {
                    addArticle(nextPage);
                } else {
                    const footer = document.querySelector('.copyRight');
                    footer.style.display = 'flex';
                }
            }
        });
    };

    createObserver(observerCallback);

    // Keyword search event
    let btn = document.querySelector('.searchKeyword_button');
    btn.addEventListener('click', function (e) {
        e.preventDefault();

        let originalArticles = document.querySelector('.load_articles');
        originalArticles.innerHTML = '';

        let kwd = document.querySelector('.searchKeyword_input');
        addKwdArticle(0, kwd.value);

        const keywordObserverCallback = entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !isLoading) {
                    if (nextPage) {
                        addKwdArticle(nextPage, kwd.value);
                    } else {
                        const footer = document.querySelector('.copyRight');
                        footer.style.display = 'flex';
                    }
                }
            });
        };

        createObserver(keywordObserverCallback);
    });

    // article click event
    let articles = document.querySelector('.load_articles');
    articles.addEventListener('click', async (event) => {
        // Check if the clicked element or its parent has the 'picture_word' class
        let targetElement = event.target;
        while (targetElement && !targetElement.classList.contains('picture_word')) {
            targetElement = targetElement.parentElement;
        }

        if (targetElement && targetElement.classList.contains('picture_word')) {
            let articleID = targetElement.id;
            console.log(`Navigating to article/${articleID}`); // For debugging

            // Ensure attrID is valid before navigating
            if (articleID) {
                window.location.assign(`article/${articleID}`);
            }
            return;
        }
    })

    // Forum click event
    let forums = document.querySelector('.forums');
    forums.addEventListener('click', async (event) => {
        if (event.target.classList.contains('forum')) {
            const keyword = event.target.textContent;
            let searchKeyword_input = document.querySelector('.searchKeyword_input');
            searchKeyword_input.value = keyword;

            let originalArticles = document.querySelector('.load_articles');
            originalArticles.innerHTML = '';

            addKwdArticle(0, keyword);

            const keywordObserverCallback = entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !isLoading) {
                        if (nextPage) {
                            addKwdArticle(nextPage, keyword);
                        } else {
                            const footer = document.querySelector('.copyRight');
                            footer.style.display = 'flex';
                        }
                    }
                });
            };

            createObserver(keywordObserverCallback);
        }
    });

    // forum Arrow click event
    let leftArrow = document.querySelector('.left-arrow');
    let rightArrow = document.querySelector('.right-arrow');
    const forumList = document.querySelector('.forums');

    if (leftArrow && rightArrow && forumList) {
        leftArrow.addEventListener('click', () => {
            forumList.scrollBy({ left: -300, behavior: 'smooth' });
        });

        rightArrow.addEventListener('click', () => {
            forumList.scrollBy({ left: 300, behavior: 'smooth' });
        });
    } else {
        console.log("One or more elements not found:", { leftArrow, rightArrow, forumList });
    }

    // Arrow hover effect
    const leftDefaultSrc = '/static/photo_icon/mrt_left_Default.png';
    const leftHoverSrc = '/static/photo_icon/mrt_left_Hovered.png';
    const rightDefaultSrc = '/static/photo_icon/mrt_right_Default.png';
    const rightHoverSrc = '/static/photo_icon/mrt_right_Hovered.png';

    leftArrow.addEventListener('mouseover', () => {
        leftArrow.src = leftHoverSrc;
    });

    leftArrow.addEventListener('mouseout', () => {
        leftArrow.src = leftDefaultSrc;
    });

    rightArrow.addEventListener('mouseover', () => {
        rightArrow.src = rightHoverSrc;
    });

    rightArrow.addEventListener('mouseout', () => {
        rightArrow.src = rightDefaultSrc;
    });

    // back to home page by clicking 熱門資訊通
    let home = document.querySelector('.home');
    home.addEventListener('click', () => {
        let clr = document.querySelector('.noArticle');
        clr.style.display = 'none';
        let footer = document.querySelector('.copyRight');
        footer.style.display = 'none';
        footer.style.position = '';
        window.location.href = '/';
    });

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

                window.location.assign('/member');

            }

        } catch (e) {
            console.log(e);
        }

    })

});
