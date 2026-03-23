function checkAll(className) {
  document.querySelectorAll("input." + className).forEach((cb) => {
    cb.checked = true;
  });
}

function uncheckAll(className) {
  document.querySelectorAll("input." + className).forEach((cb) => {
    cb.checked = false;
  });
}
