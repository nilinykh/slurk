if (element.event === 'text_message') {
    if (element.html) {
        $.getScript('https://cdn.jsdelivr.net/npm/showdown@1.9.0/dist/showdown.min.js', () => {
            const converter = new showdown.Converter();
            display_message(
                element.user,
                element.date_modified,
                converter.makeHtml(element.message),
                element.receiver !== null,
                true);
        });
    } else {
        display_message(
            element.user,
            element.date_modified,
            element.message,
            element.receiver !== null);
    }
} else if (element.event === "image_message") {
    display_image(
        element.user,
        element.date_modified,
        element.url,
        element.width,
        element.height,
        element.receiver !== null);
}
