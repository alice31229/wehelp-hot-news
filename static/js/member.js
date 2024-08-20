// dom collect articles for loop
function eventsDomTree(events) {
    const collect_articles = document.querySelector('.img_collection');

    events.forEach(event => {

        const container = document.createElement('div');
        container.setAttribute('class', 'thousand_twoHundred');

        const left = document.createElement('div');
        left.setAttribute('class', 'left');

        // wordcloud img
        const wcImgDiv = document.createElement('div');
        wcImgDiv.setAttribute('class', 'img');

        const wcImg = document.createElement('img');
        wcImg.setAttribute('class', 'article_img');
        wcImg.setAttribute('alt', 'wordcloud');
        wcImg.src = event.wordcloud;

        wcImgDiv.appendChild(wcImg);

        // collect info
        const articleInfo = document.createElement('div');
        articleInfo.setAttribute('class', 'article_info');

        const title = document.createElement('div');
        title.setAttribute('id', event.id);
        title.setAttribute('class', 'title');
        title.textContent = `標題：${event.title}`;

        const summary = document.createElement('div');
        summary.setAttribute('class', 'summary');

        function createMarginBottomDiv(prefixText, value, id) {
            const marginBottom = document.createElement('div');
            marginBottom.setAttribute('class', 'marginBottom');
          
            const prefixSpan = document.createElement('span');
            prefixSpan.setAttribute('class', 'common_style_site_up');
            prefixSpan.textContent = prefixText;
          
            const valueSpan = document.createElement('span');
            valueSpan.setAttribute('class', 'no_bold_style_up');
            valueSpan.setAttribute('id', id);
            valueSpan.textContent = value;
          
            marginBottom.appendChild(prefixSpan);
            marginBottom.appendChild(valueSpan);
          
            return marginBottom;
        }
          
        function createMarginBottomDivWithLink(prefixText, url, id) {
            const marginBottom = document.createElement('div');
            marginBottom.setAttribute('class', 'marginBottom');
            
            const prefixSpan = document.createElement('span');
            prefixSpan.setAttribute('class', 'common_style_site_up');
            prefixSpan.textContent = prefixText;
            
            const link = document.createElement('a');
            link.setAttribute('class', 'no_bold_style_up');
            link.setAttribute('id', id);
            link.href = url;
            link.textContent = url;
            
            const URLicon = document.createElement('img');
            URLicon.src = '/static/photo_icon/article_link.png';
            URLicon.setAttribute('class', 'url-icon');
            link.appendChild(URLicon);
            
            marginBottom.appendChild(prefixSpan);
            marginBottom.appendChild(link);
            
            return marginBottom;
        }

        // forum
        const marginBottomForum = createMarginBottomDiv('類型：', event.forum, 'forum');
        // resource
        const marginBottomResource = createMarginBottomDiv('來源：', event.resource, 'resource');
        // date
        const marginBottomDate = createMarginBottomDiv('日期：', event.date, 'date');
        // url
        const marginBottomURL = createMarginBottomDivWithLink('出處：', event.url, 'url');

        summary.appendChild(marginBottomForum);
        summary.appendChild(marginBottomResource);
        summary.appendChild(marginBottomDate);
        summary.appendChild(marginBottomURL);

        articleInfo.appendChild(title);
        articleInfo.appendChild(summary);

        left.appendChild(wcImgDiv);
        left.appendChild(articleInfo);

        // delete click
        const garbageCanDiv = document.createElement('div');
        garbageCanDiv.setAttribute('class', 'garbage_can');

        const garbageCan = document.createElement('img');
        garbageCan.setAttribute('class', 'article_id');
        garbageCan.setAttribute('alt', 'deleteRecord');
        garbageCan.src = '/static/photo_icon/delete-y-o.png';
        garbageCan.id = event.id;

        garbageCanDiv.appendChild(garbageCan);

        // sep line
        const hr = document.createElement('hr');
        hr.setAttribute('id', 'collect_line');
        hr.setAttribute('class', 'line');

        container.appendChild(left);
        container.appendChild(garbageCanDiv);
        //container.appendChild(hr);

        collect_articles.appendChild(container);
        collect_articles.appendChild(hr);

    })

}


// load previous booking history
async function LoadCollectionRecords() {

    const token = localStorage.getItem("authToken");

    // garbage can need to add corresponding article id for delete tab work
    try {

        const getResponse = await fetch('/api/collect', {
            method: 'GET',
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }

        });

        let result = await getResponse.json();

        // member name
        let memberInfo = await fetch('/api/user/auth', {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        })


        if (result.status === 403) { // not log in

            window.location.href = '/';

        } 
        
        if (result.data){ // have article collect record

            showElements();

            if (memberInfo.ok) {
                let memberData = await memberInfo.json();
                let memberInfoLS = JSON.parse(localStorage.getItem("memberInfo"));
                if (memberData.data && !memberInfoLS) {
                    document.querySelector('.title_style_up').textContent = `您好，${memberData.data.name}，收藏的文章如下：`;
                }else {
                    document.querySelector('.title_style_up').textContent = `您好，${memberInfoLS.name}，收藏的文章如下：`;
                }
            }

            eventsDomTree(result.data);
            

        } else { // no collection record

            let showNoCollection = document.querySelector('.noCollection');
            showNoCollection.style.display = 'flex';

            if (memberInfo.ok) {
                let memberData = await memberInfo.json();
                let memberInfoLS = JSON.parse(localStorage.getItem("memberInfo"));
                if (memberData.data && !memberInfoLS) {
                    document.querySelector('.title_style_up').textContent = `您好，${memberData.data.name}，收藏的文章如下：`;
                }else {
                    document.querySelector('.title_style_up').textContent = `您好，${memberInfoLS.name}，收藏的文章如下：`;
                }
                // let memberData = await memberInfo.json();
                // if (memberData.data) {
                //     document.querySelector('.title_style_up').textContent = `您好，${memberData.data.name}，收藏的文章如下：`;
                // }
            }

            // hideElements();

        }

    } catch(e) {
        console.log('load article collect error');
    }

}

function showPageContent() {
    // Implement this function to show your main page content
    const mainContent = document.querySelector('.main-content');
    mainContent.style.display = 'block';
}


async function checkLogIn() {
    const token = localStorage.getItem("authToken");

    try {
        const getLogInResponse = await fetch('/api/user/auth', {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        if (getLogInResponse.ok) {
            const data = await getLogInResponse.json();
            if (data.data) {
                return true;
            } else {
                return false;
            }
        }else {
            return false;
        }

    }catch (e) {
        return false;
    }
}


function showElements() {

    let showNoCollection = document.querySelector('.noCollection');

    showNoCollection.classList.add('hidden');

}

function ShowNoCollect() {

    let showNoCollection = document.querySelector('.noCollection');
    showNoCollection.display('flex');
    showNoCollection.classList.remove('hidden');

}


// loading before the data fetch back from db and backend
window.addEventListener("load", () => {
    const loader = document.querySelector(".loader");
    loader.classList.add('loader--hidden');
    // setTimeout(() => {
    //     loader.classList.add('loader--hidden');
    // }, 1500);
});

// clear any popup input value
function clearInputValue() {
    document.querySelector('#usernameID').value = '';
    document.querySelector('#usernameID-enroll').value = '';
    document.querySelector('#passwordID').value = '';
    document.querySelector('#passwordID-enroll').value = '';
    document.querySelector('#nameID-enroll').value = '';
    document.querySelector('#emailID-enroll').value = '';
    document.querySelector('#nameID-edit').value = '';
    document.querySelector('#emailID-edit').value = '';
    document.querySelector('#selfieInput').value = '';
}
// adjust sign in / enroll / edit result height
function adjustHeightAll() {
    document.querySelector('.pop-up-sign-in').style.height = '275px';
    document.querySelector('.pop-up-enroll').style.height = '392px';
    document.querySelector('.pop-up-edit').style.height = '362px';
}


document.addEventListener("DOMContentLoaded", async function () {

    // collect page detail: member_name, title, date, resource, forum, article_img, link
    // check the member has collected articles before or not -> articles info ; no record
    
    const memberInfo = JSON.parse(localStorage.getItem("memberInfo"));
    if (memberInfo) {

        // check log in or not then render
        if (await checkLogIn()) {
            
            LoadCollectionRecords().then(() => {

                // back to homePage
                let title = document.querySelector('.home');
                title.addEventListener('click', () => {
                    window.location.href = '/';
                })


                // log out -> remove token -> back to homePage
                let logOut = document.querySelector('#signInEnroll');
                logOut.addEventListener('click', () => {

                    localStorage.removeItem("authToken");
                    localStorage.removeItem("memberInfo");
                    window.location.href = '/';

                })


                // edit member info
                let editInfo = document.querySelector('#editAccount');
                editInfo.addEventListener("click", function() {

                    if (checkLogIn()) {
                        
                        // show edit info dialog
                        let edit = document.querySelector('.pop-background-color-edit');
                        let closeEdit = document.querySelector('.close-pop-edit');
                            
                        const fadeElement = document.getElementById('fade-edit');
                        fadeElement.classList.add('show');
                        edit.style.display = 'flex';
                        
                        closeEdit.addEventListener('click', function(){
                            const fadeElement = document.getElementById('fade-edit');
                            fadeElement.classList.remove('show');
                            clearInputValue();
                            adjustHeightAll();
                            edit.style.display = 'none';
                        })
                        edit.addEventListener('click', function(event) {
                            if (event.target === edit) {

                                const fadeElement = document.getElementById('fade-edit');
                                fadeElement.classList.remove('show');
                                // if error message shows -> hide
                                let errorShow = document.querySelector('.message-edit');
                                errorShow.style.display = 'none';
                                clearInputValue();
                                adjustHeightAll();
                                edit.style.display = 'none';
                    
                            }
                        })
                        // edit btn click await
                        const editForm = document.getElementById("edit");
                        editForm.addEventListener('submit', async function(event) {
                            
                            event.preventDefault();

                            if (checkLogIn()) {

                                let name = document.querySelector('#nameID-edit').value;
                                let email = document.querySelector('#emailID-edit').value;
                                let file = document.querySelector('#selfieInput').files[0];

                                let formData = new FormData();
                                formData.append('name', name);
                                formData.append('email', email);
                                formData.append('file', file);

                                try {
                                    const token = localStorage.getItem("authToken");
                                    const editResponse = await fetch('/api/member', {
                                        method: "PUT",
                                        body: formData,
                                        headers: {
                                            "Authorization": `Bearer ${token}`
                                        }
                                    })

                                    if (editResponse.ok) {
                                        // edit ok, close the edit dialog and show changes
                                        const data = await editResponse.json();

                                        if (data.ok) {
                                            localStorage.setItem("memberInfo", JSON.stringify(data.member_update));
                                            document.querySelector('.title_style_up').textContent = `您好，${data.member_update.name}，收藏的文章如下：`
                                            clearInputValue();
                                            adjustHeightAll();
                                            edit.style.display = 'none';
                                            //window.location.reload('/member');
                                        } else {
                                            //document.querySelector('.pop-up-edit').style.height = '412px';
                                            let showErrorMessage = document.querySelector('.message-edit');
                                            showErrorMessage.style.display = 'block';
                                            showErrorMessage.textContent = data.message;
                                        }


                                    } else {
                                        // edit error, show eror message
                                        console.log('edit error...');
                                    }

                                } catch (error) {
                                    console.error("Edit failed:", error);
                                }
                            } else{
                                // Token is invalid or expired
                                localStorage.removeItem("authToken");
                                localStorage.removeItem("memberInfo");
                                window.location.assign('/');
                            }
                                
                        })


                    } else {
                        // Token is invalid or expired
                        localStorage.removeItem("authToken");
                        localStorage.removeItem("memberInfo");
                        
                        // show sign in dialog
                        const fadeElement = document.getElementById('fade-sign-in');
                        fadeElement.classList.add('show');
                        let signIn = document.querySelector('.pop-background-color-sign-in');
                        signIn.style.display = 'flex';
                    };

                })

                
                // delete collect article by clicking garbage can icon
                let deleteCollections = document.querySelectorAll('.garbage_can');
                if (deleteCollections) { // 檢查delete garbage_can是否存在 避免錯誤
                    deleteCollections.forEach(button => {
                        // 為每個垃圾桶圖示添加事件監聽器
                        button.addEventListener('click', async (event) => {

                            event.preventDefault();

                            // check log in or not
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
                        
                                    let signIn = document.querySelector('.pop-background-color-sign-in');
                                    signIn.style.display = 'flex';

                        
                                } else {

                                    let targetElementID = event.target.id;
                                    targetElementID = targetElementID.toString();
                                    if (targetElementID) {
                                        //console.log(`Get article/${targetElementID}`); // For debugging

                                        // Ensure attrID is valid before navigating
                                        let memberID = result.data.id;
                                        memberID = memberID.toString()
                                        const deleteResponse = await fetch('/api/collect', {
                                            method: 'DELETE',
                                            body: JSON.stringify({
                                                memberId: memberID,
                                                articleId: targetElementID
                                            }),
                                            headers: {
                                                "Authorization": `Bearer ${token}`,
                                                "Content-Type": "application/json"
                                            }

                                        });

                                        if (deleteResponse.ok) {

                                            window.location.reload();

                                        }

                                        return;
                                    }
                                }
                            } catch(e) {
                                console.log('delete collect error');
                            }
                        })
                    })

                }

                // click collect article event
                // let deleteCollections = document.querySelectorAll('.garbage_can');
                // if (deleteCollections) { // 檢查delete garbage_can是否存在 避免錯誤
                //     deleteCollections.forEach(button => {
                let articles = document.querySelectorAll('.title');
                console.log(articles);
                if (articles){
                    articles.forEach(article => {
                        article.addEventListener('click', (event) => {
                    
                            let targetElementID = event.target.id;
                            console.log(targetElementID);
            
                            if (targetElementID) {
                                console.log(`Navigating to article/${targetElementID}`); // For debugging
            
                                // Ensure attrID is valid before navigating
                                window.location.assign(`article/${targetElementID}`);
                                return;
                            }
                        })
                    })
                    
                }
                

            })



        } else {
            // Token is invalid or expired
            localStorage.removeItem("authToken");
            localStorage.removeItem("memberInfo");
            window.location.assign('/');
        };

    } else{

        // check log in or not then render
        if (await checkLogIn()) {
            
            LoadCollectionRecords().then(() => {

                // back to homePage
                let title = document.querySelector('.home');
                title.addEventListener('click', () => {
                    window.location.href = '/';
                })


                // log out -> remove token -> back to homePage
                let logOut = document.querySelector('#signInEnroll');
                logOut.addEventListener('click', () => {

                    localStorage.removeItem("authToken");
                    localStorage.removeItem("memberInfo");
                    window.location.href = '/';

                })


                // edit member info
                let editInfo = document.querySelector('#editAccount');
                editInfo.addEventListener("click", function() {

                    if (checkLogIn()) {
                        
                        // show edit info dialog
                        let edit = document.querySelector('.pop-background-color-edit');
                        let closeEdit = document.querySelector('.close-pop-edit');
                            
                        const fadeElement = document.getElementById('fade-edit');
                        fadeElement.classList.add('show');
                        edit.style.display = 'flex';
                        
                        closeEdit.addEventListener('click', function(){
                            const fadeElement = document.getElementById('fade-edit');
                            fadeElement.classList.remove('show');
                            clearInputValue();
                            adjustHeightAll();
                            edit.style.display = 'none';
                        })
                        edit.addEventListener('click', function(event) {
                            if (event.target === edit) {

                                const fadeElement = document.getElementById('fade-edit');
                                fadeElement.classList.remove('show');
                                // if error message shows -> hide
                                let errorShow = document.querySelector('.message-edit');
                                errorShow.style.display = 'none';
                                clearInputValue();
                                adjustHeightAll();
                                edit.style.display = 'none';
                    
                            }
                        })
                        // edit btn click await
                        const editForm = document.getElementById("edit");
                        editForm.addEventListener('submit', async function(event) {
                            
                            event.preventDefault();

                            if (checkLogIn()) {

                                let name = document.querySelector('#nameID-edit').value;
                                let email = document.querySelector('#emailID-edit').value;
                                let file = document.querySelector('#selfieInput').files[0];

                                let formData = new FormData();
                                formData.append('name', name);
                                formData.append('email', email);
                                formData.append('file', file);

                                try {
                                    const token = localStorage.getItem("authToken");
                                    const editResponse = await fetch('/api/member', {
                                        method: "PUT",
                                        body: formData,
                                        headers: {
                                            "Authorization": `Bearer ${token}`
                                        }
                                    })

                                    if (editResponse.ok) {
                                        // edit ok, close the edit dialog and show changes
                                        const data = await editResponse.json();

                                        if (data.ok) {
                                            localStorage.setItem("memberInfo", JSON.stringify(data.member_update));
                                            document.querySelector('.title_style_up').textContent = `您好，${data.member_update.name}，收藏的文章如下：`
                                            clearInputValue();
                                            adjustHeightAll();
                                            edit.style.display = 'none';
                                            //window.location.reload('/member');
                                        } else {
                                            //document.querySelector('.pop-up-edit').style.height = '412px';
                                            let showErrorMessage = document.querySelector('.message-edit');
                                            showErrorMessage.style.display = 'block';
                                            showErrorMessage.textContent = data.message;
                                        }


                                    } else {
                                        // edit error, show eror message
                                        console.log('edit error...');
                                    }

                                } catch (error) {
                                    console.error("Edit failed:", error);
                                }
                            } else{
                                // Token is invalid or expired
                                localStorage.removeItem("authToken");
                                localStorage.removeItem("memberInfo");
                                window.location.assign('/');
                            }
                                
                        })


                    } else {
                        // Token is invalid or expired
                        localStorage.removeItem("authToken");
                        localStorage.removeItem("memberInfo");
                        
                        // show sign in dialog
                        const fadeElement = document.getElementById('fade-sign-in');
                        fadeElement.classList.add('show');
                        let signIn = document.querySelector('.pop-background-color-sign-in');
                        signIn.style.display = 'flex';
                    };

                })

                
                // delete collect article by clicking garbage can icon
                let deleteCollections = document.querySelectorAll('.garbage_can');
                if (deleteCollections) { // 檢查delete garbage_can是否存在 避免錯誤
                    deleteCollections.forEach(button => {
                        // 為每個垃圾桶圖示添加事件監聽器
                        button.addEventListener('click', async (event) => {

                            event.preventDefault();

                            // check log in or not
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
                        
                                    let signIn = document.querySelector('.pop-background-color-sign-in');
                                    signIn.style.display = 'flex';

                        
                                } else {

                                    let targetElementID = event.target.id;
                                    targetElementID = targetElementID.toString();
                                    if (targetElementID) {
                                        //console.log(`Get article/${targetElementID}`); // For debugging

                                        // Ensure attrID is valid before navigating
                                        let memberID = result.data.id;
                                        memberID = memberID.toString()
                                        const deleteResponse = await fetch('/api/collect', {
                                            method: 'DELETE',
                                            body: JSON.stringify({
                                                memberId: memberID,
                                                articleId: targetElementID
                                            }),
                                            headers: {
                                                "Authorization": `Bearer ${token}`,
                                                "Content-Type": "application/json"
                                            }

                                        });

                                        if (deleteResponse.ok) {

                                            window.location.reload();

                                        }

                                        return;
                                    }
                                }
                            } catch(e) {
                                console.log('delete collect error');
                            }
                        })
                    })

                }

                // click collect article event
                let articles = document.querySelector('.title');
                if (articles){
                    articles.addEventListener('click', async (event) => {
                    
                        let targetElementID = event.target.id;
        
                        if (targetElementID) {
                            console.log(`Navigating to article/${targetElementID}`); // For debugging
        
                            // Ensure attrID is valid before navigating
                            window.location.assign(`article/${targetElementID}`);
                            return;
                        }
                    })
                }
                

            })



        } else {
            // Token is invalid or expired
            localStorage.removeItem("authToken");
            localStorage.removeItem("memberInfo");
            window.location.assign('/');
        };

    }

})