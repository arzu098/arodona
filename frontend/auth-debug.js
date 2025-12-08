/*
Add this to the browser console to debug authentication issues:

// Check what's stored in localStorage
console.log('=== Auth Debug Info ===');
console.log('Access Token:', localStorage.getItem('accessToken'));
console.log('User:', localStorage.getItem('user'));
console.log('User Role:', localStorage.getItem('userRole'));
console.log('User Email:', localStorage.getItem('userEmail'));

// Clear all auth data if needed
function clearAuthDebug() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('user');
  localStorage.removeItem('userRole'); 
  localStorage.removeItem('userEmail');
  console.log('Auth data cleared');
  location.reload();
}

// Call clearAuthDebug() if you want to reset authentication
*/

// Alternatively, you can add this button to manually clear auth:
function addClearAuthButton() {
  const button = document.createElement('button');
  button.innerText = 'Clear Auth & Reload';
  button.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;background:red;color:white;padding:10px;border:none;cursor:pointer;';
  button.onclick = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole'); 
    localStorage.removeItem('userEmail');
    location.reload();
  };
  document.body.appendChild(button);
}

// Uncomment to add the button:
// addClearAuthButton();