// 选项卡切换功能
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const successMessage = document.getElementById('success-message');
const successText = document.getElementById('success-text');
const errorMessage = document.getElementById('error-message');
const errorText = document.getElementById('error-text');

// 选项卡切换
function switchTab(tabId) {
    // 隐藏所有选项卡内容
    tabContents.forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有选项卡按钮的激活状态
    tabBtns.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的选项卡内容
    document.getElementById(`${tabId}-tab`).classList.add('active');
    
    // 激活选中的选项卡按钮
    event.currentTarget.classList.add('active');
    
    // 隐藏消息
    successMessage.style.display = 'none';
    errorMessage.style.display = 'none';
}

// 为选项卡按钮添加点击事件
if (tabBtns.length > 0) {
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
}

// 登录表单处理
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 获取表单数据
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        // 隐藏之前的消息
        successMessage.style.display = 'none';
        errorMessage.style.display = 'none';
        
        try {
            // 发送登录请求
            const response = await fetch('http://localhost:8000/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // 登录成功
                successText.textContent = '✓ 登录成功';
                successMessage.style.display = 'block';
                // 保存token到localStorage
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('token_type', data.token_type);
                
                // 显示token和响应信息
                const responseInfo = document.createElement('div');
                responseInfo.style.marginTop = '10px';
                responseInfo.style.padding = '10px';
                responseInfo.style.backgroundColor = '#f0f8ff';
                responseInfo.style.border = '1px solid #b8daff';
                responseInfo.style.borderRadius = '4px';
                responseInfo.style.fontFamily = 'monospace';
                responseInfo.style.fontSize = '12px';
                responseInfo.style.whiteSpace = 'pre-wrap';
                responseInfo.textContent = `Token: ${data.access_token}\n\n完整响应: ${JSON.stringify(data, null, 2)}`;
                successMessage.appendChild(responseInfo);
                
                // 3秒后可以跳转到其他页面
                setTimeout(() => {
                    // 这里可以添加页面跳转逻辑
                    console.log('登录成功，准备跳转');
                }, 3000);
            } else {
                // 登录失败
                errorText.textContent = data.detail || '登录失败，请检查邮箱和密码';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            // 网络错误
            errorText.textContent = '网络错误，请稍后重试';
            errorMessage.style.display = 'block';
            console.error('登录请求失败:', error);
        }
    });
}

// 注册表单处理
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 获取表单数据
        const email = document.getElementById('register-email').value;
        const nickname = document.getElementById('register-nickname').value;
        const password = document.getElementById('register-password').value;
        
        // 隐藏之前的消息
        successMessage.style.display = 'none';
        errorMessage.style.display = 'none';
        
        try {
            // 发送注册请求
            const response = await fetch('http://localhost:8000/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, nickname, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // 注册成功
                successText.textContent = '✓ 注册成功，请登录';
                successMessage.style.display = 'block';
                
                // 显示响应信息
                const responseInfo = document.createElement('div');
                responseInfo.style.marginTop = '10px';
                responseInfo.style.padding = '10px';
                responseInfo.style.backgroundColor = '#f0f8ff';
                responseInfo.style.border = '1px solid #b8daff';
                responseInfo.style.borderRadius = '4px';
                responseInfo.style.fontFamily = 'monospace';
                responseInfo.style.fontSize = '12px';
                responseInfo.style.whiteSpace = 'pre-wrap';
                responseInfo.textContent = `完整响应: ${JSON.stringify(data, null, 2)}`;
                successMessage.appendChild(responseInfo);
                
                // 3秒后切换到登录选项卡
                setTimeout(() => {
                    document.querySelector('[data-tab="login"]').click();
                }, 3000);
            } else {
                // 注册失败
                errorText.textContent = data.detail || '注册失败，请稍后重试';
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            // 网络错误
            errorText.textContent = '网络错误，请稍后重试';
            errorMessage.style.display = 'block';
            console.error('注册请求失败:', error);
        }
    });
}

// 找回密码表单处理
const forgotForm = document.getElementById('forgot-form');
if (forgotForm) {
    forgotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 获取表单数据
        const email = document.getElementById('forgot-email').value;
        
        // 隐藏之前的消息
        successMessage.style.display = 'none';
        errorMessage.style.display = 'none';
        
        try {
            // 模拟找回密码请求
            // 注意：后端尚未实现找回密码功能
            successText.textContent = '✓ 重置链接已发送到您的邮箱';
            successMessage.style.display = 'block';
        } catch (error) {
            // 网络错误
            errorText.textContent = '网络错误，请稍后重试';
            errorMessage.style.display = 'block';
            console.error('找回密码请求失败:', error);
        }
    });
}

// 处理SSO回调
function handleSsoCallback() {
    // 检查URL中是否有SSO回调参数
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const tokenType = urlParams.get('token_type');
    const refreshToken = urlParams.get('refresh_token');
    const expiresIn = urlParams.get('expires_in');
    
    if (accessToken) {
        // 保存token到localStorage
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('token_type', tokenType || 'bearer');
        localStorage.setItem('refresh_token', refreshToken);
        localStorage.setItem('expires_in', expiresIn);
        
        // 显示登录成功消息
        if (successMessage && successText) {
            successText.textContent = '✓ 第三方登录成功';
            successMessage.style.display = 'block';
            
            // 显示token信息
            const responseInfo = document.createElement('div');
            responseInfo.style.marginTop = '10px';
            responseInfo.style.padding = '10px';
            responseInfo.style.backgroundColor = '#f0f8ff';
            responseInfo.style.border = '1px solid #b8daff';
            responseInfo.style.borderRadius = '4px';
            responseInfo.style.fontFamily = 'monospace';
            responseInfo.style.fontSize = '12px';
            responseInfo.style.whiteSpace = 'pre-wrap';
            responseInfo.textContent = `Token: ${accessToken}\n\n完整响应: ${JSON.stringify({ access_token: accessToken, token_type: tokenType, refresh_token: refreshToken, expires_in: expiresIn }, null, 2)}`;
            successMessage.appendChild(responseInfo);
        }
        
        // 3秒后可以跳转到其他页面
        setTimeout(() => {
            console.log('第三方登录成功，准备跳转');
        }, 3000);
        
        // 清除URL中的参数，使页面更整洁
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

// 处理SSO登录
function handleSsoLogin(provider) {
    const redirectUri = 'http://localhost:8080';
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    // 发送请求获取授权URL
    fetch(`http://localhost:8000/api/v1/auth/sso/${provider}/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`)
        .then(response => response.json())
        .then(data => {
            if (data.authorize_url) {
                // 重定向到授权URL
                window.location.href = data.authorize_url;
            } else {
                console.error('获取授权URL失败:', data);
                if (errorMessage && errorText) {
                    errorText.textContent = '获取授权URL失败';
                    errorMessage.style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('网络错误:', error);
            if (errorMessage && errorText) {
                errorText.textContent = '网络错误，请稍后重试';
                errorMessage.style.display = 'block';
            }
        });
}

// 页面加载时检查是否有SSO回调
window.addEventListener('load', handleSsoCallback);

