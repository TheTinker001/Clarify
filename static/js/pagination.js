document.addEventListener("DOMContentLoaded", () => {
  for (const link of document.querySelectorAll(".page-jump-trigger")) {
    link.onclick = (event) => {
      event.preventDefault();
      const max_pages = +link.dataset.maxPages;
      const querystring = link.dataset.querystring || "";
      const page = prompt(`Select page: (1 ~ ${max_pages})`);

      if (page && !isNaN(page) && page >= 1 && page <= max_pages) {
        let url = window.location.pathname + "?";

        if (querystring) url += querystring + "&";
        window.location = url + "page=" + page;
      }
    };
  }
});
