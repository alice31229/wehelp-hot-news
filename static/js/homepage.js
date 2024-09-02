function eventsDomTree(events) {
    const more_articles = document.querySelector('.load_articles');

    events.forEach(event => {
        // Create picture div
        const wcAndInfo = document.createElement('div');
        wcAndInfo.setAttribute('class', 'wcAndInfo');
        wcAndInfo.setAttribute('id', event.id);

        // img at left part relative to article info
        const wc = document.createElement('img');
        wc.src = event.wordcloud;
        wc.setAttribute('class', 'wc-img');

        // article info at right part relative to wc-img
        const articleInfo = document.createElement('div');
        articleInfo.setAttribute('class', 'articleInfo');

        let title = document.createElement('div');
        title.setAttribute('class', 'title');
        title.textContent = event.title;

        let category = document.createElement('div');
        category.setAttribute('class', 'category');
        category.textContent = event.category;

        let resource = document.createElement('div');
        resource.setAttribute('class', 'resource');
        resource.textContent = event.resource;

        let date = document.createElement('div');
        date.setAttribute('class', 'date');
        date.textContent = event.date;

        articleInfo.appendChild(title);
        articleInfo.appendChild(category);
        articleInfo.appendChild(resource);
        articleInfo.appendChild(date);

        // append img and article info under wcAndInfo
        wcAndInfo.appendChild(wc);
        wcAndInfo.appendChild(articleInfo);

        more_articles.appendChild(wcAndInfo);
    });
}

// append hot keywords to recommend users
async function AppendHotKwd() { // /api/hotkeywords
    try {
        const postResponse = await fetch('/api/hotkeywords');
        const postData = await postResponse.text();
        const forum_result = JSON.parse(postData);
        let infos = forum_result.data;

        let appendHere = document.querySelector('.hotWords');

        infos.forEach(f => {
            const newForumDiv = document.createElement('div');
            newForumDiv.textContent = f;
            newForumDiv.className = 'hotWord';

            appendHere.appendChild(newForumDiv);
        });
    } catch (e) {
        console.error('Error fetching Forums:', e);
    }
}

// add article category to the filter options -> call /api/filter-category
async function AddArticleCategory() { 
    try {
        const postResponse = await fetch('/api/filter-category');
        const postData = await postResponse.text();
        const category_result = JSON.parse(postData);
        let infos = category_result.data;

        let AppendCategory = document.querySelector('.AppendCategory');
        infos.forEach(event => {
            let inputCheckbox = document.createElement('input');
            inputCheckbox.setAttribute('type', 'checkbox');
            inputCheckbox.setAttribute('id', 'categories');
            inputCheckbox.setAttribute('name', 'category');
            inputCheckbox.setAttribute('value', event.id);

            let CheckboxLabel = document.createElement('label');
            CheckboxLabel.setAttribute('for', 'resources');
            CheckboxLabel.setAttribute('class', 'innerLabel');
            CheckboxLabel.textContent = event.category;

            AppendCategory.appendChild(inputCheckbox);
            AppendCategory.appendChild(CheckboxLabel);
        })

    } catch (e) {
        console.error('Error fetching Category:', e);
    }
}

// provide overall and each resource category distribution
async function ProvideCategoryDist() {

} 

function submitSelection() {

    const keyword = document.querySelector('.searchKeyword_input').value;
    const resources = Array.from(document.querySelectorAll('input[name="resource"]:checked')).map(input => input.value);
    const categories = Array.from(document.querySelectorAll('input[name="category"]:checked')).map(input => input.value);
    const dates = Array.from(document.querySelectorAll('input[name="date"]:checked')).map(input => input.value);

    // resources -> ptt storm businesstoday udn
    // dates -> 當日 三天內 一週內

    const data = {
        keyword,
        resources,
        categories,
        dates
    };

    fetch('/api/filter-articles-search', {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        
        eventsDomTree(data);
        //console.log(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });

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

// change to filter type
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
    AppendHotKwd();
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


    // Category click event
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
    let leftArrow = document.querySelector('#category-left');
    let rightArrow = document.querySelector('#category-right');
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
    const leftDefaultSrc = '/static/photo_icon/left_Default.png';
    const leftHoverSrc = '/static/photo_icon/left_Hovered.png';
    const rightDefaultSrc = '/static/photo_icon/right_Default.png';
    const rightHoverSrc = '/static/photo_icon/right_Hovered.png';

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

    ///////////////////

    // HotKeywords click event
    let hotWords = document.querySelector('.hotWords');
    hotWords.addEventListener('click', async (event) => {
        if (event.target.classList.contains('hotWord')) {
            const keyword = event.target.textContent;
            let searchKeyword_input = document.querySelector('.searchKeyword_input');
            searchKeyword_input.value = keyword;

            let originalArticles = document.querySelector('.load_articles');
            originalArticles.innerHTML = '';

            addKwdArticle(0, keyword);

            const hotKeywordObserverCallback = entries => {
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

            createObserver(hotKeywordObserverCallback);
        }
    });

    // forum Arrow click event
    let hotKwdleftArrow = document.querySelector('#kwds-left');
    let hotKwdrightArrow = document.querySelector('#kwds-right');
    const hotKwdList = document.querySelector('.hotWords');

    if (hotKwdleftArrow && hotKwdrightArrow && hotKwdList) {
        hotKwdleftArrow.addEventListener('click', () => {
            hotKwdList.scrollBy({ left: -300, behavior: 'smooth' });
        });

        hotKwdrightArrow.addEventListener('click', () => {
            hotKwdList.scrollBy({ left: 300, behavior: 'smooth' });
        });
    } else {
        console.log("One or more elements not found:", { hotKwdleftArrow, hotKwdrightArrow, hotKwdList });
    }

    // Arrow hover effect
    const hotKwdleftDefaultSrc = '/static/photo_icon/left_Default.png';
    const hotKwdleftHoverSrc = '/static/photo_icon/left_Hovered.png';
    const hotKwdrightDefaultSrc = '/static/photo_icon/right_Default.png';
    const hotKwdrightHoverSrc = '/static/photo_icon/right_Hovered.png';

    hotKwdleftArrow.addEventListener('mouseover', () => {
        hotKwdleftArrow.src = hotKwdleftHoverSrc;
    });

    hotKwdleftArrow.addEventListener('mouseout', () => {
        hotKwdleftArrow.src = hotKwdleftDefaultSrc;
    });

    hotKwdrightArrow.addEventListener('mouseover', () => {
        hotKwdrightArrow.src = hotKwdrightHoverSrc;
    });

    hotKwdrightArrow.addEventListener('mouseout', () => {
        hotKwdrightArrow.src = hotKwdrightDefaultSrc;
    });


    ///////////////////

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
