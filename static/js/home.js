//Stok Filtreleme:

//Stok Filter input listener:
document.getElementById("table-filter-input").addEventListener("input", function () {
  const input = this.value.toLowerCase();
  const table = document.getElementById("data-table");
  const rows = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
  const colIndex = document.getElementById("filter-column").value;

  for (let i = 0; i < rows.length; i++) {
    let show = false;
    const cells = rows[i].getElementsByTagName("td");

    if (colIndex === "all") {
      for (let cell of cells) {
        if (cell.textContent.toLowerCase().includes(input)) {
          show = true;
          break;
        }
      }
    } else {
      if (cells[colIndex] && cells[colIndex].textContent.toLowerCase().includes(input)) {
        show = true;
      }
    }

    rows[i].style.display = show ? "" : "none";
  }
});

//Comcobox seçim sonrası filtreleme sıfırla ve listener tetikle:
document.getElementById('filter-column').addEventListener('change', function () {

  const input = document.getElementById("table-filter-input");
  input.dispatchEvent(new Event("input"));
});

//Çarpı sonrası filtreleme sıfırla ve listener tetikle:
document.getElementById("clear-filter").addEventListener("click", function () {
  const input = document.getElementById("table-filter-input");
  input.value = "";
  input.dispatchEvent(new Event("input"));
});

