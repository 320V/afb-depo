// Toggle the submenu visibility and icon rotation
function toggleSubMenu(menuId) {
    var submenu = document.getElementById(menuId);
    var toggleButton = submenu.previousElementSibling;  // The <a> tag that toggles the submenu

    if (submenu.classList.contains('submenu-open')) {
        submenu.classList.remove('submenu-open');
        toggleButton.classList.remove('active');
    } else {
        submenu.classList.add('submenu-open');
        toggleButton.classList.add('active');
    }
}
