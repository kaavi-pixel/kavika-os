registerShortcut("KavikaToggle", "Switch Kavi'ka preview workspace", "Meta+F12", function () {
    const list = workspace.desktops;
    if (list.length < 2) {
        return;
    }
    workspace.currentDesktop = workspace.currentDesktop.id === list[0].id ? list[1] : list[0];
});
