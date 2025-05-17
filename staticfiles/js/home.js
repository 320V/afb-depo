$(document).ready(function() {
    // Stok Filtreleme
    const $tableFilterInput = $("#table-filter-input");
    const $filterColumn = $("#filter-column");
    const $clearFilter = $("#clear-filter");

    if ($tableFilterInput.length) {
        $tableFilterInput.on("input", function() {
            const input = this.value.toLowerCase();
            const $table = $("#data-table");
            const $rows = $table.find("tbody tr");
            const colIndex = $filterColumn.val();

            $rows.each(function() {
                let show = false;
                const $cells = $(this).find("td");

                if (colIndex === "all") {
                    $cells.each(function() {
                        if ($(this).text().toLowerCase().includes(input)) {
                            show = true;
                            return false; // break the loop
                        }
                    });
                } else {
                    if ($cells.eq(colIndex).length && $cells.eq(colIndex).text().toLowerCase().includes(input)) {
                        show = true;
                    }
                }

                $(this).toggle(show);
            });
        });
    }

    // Comcobox seçim sonrası filtreleme sıfırla
    if ($filterColumn.length) {
        $filterColumn.on("change", function() {
            $tableFilterInput.trigger("input");
        });
    }

    // Çarpı sonrası filtreleme sıfırla
    if ($clearFilter.length) {
        $clearFilter.on("click", function() {
            $tableFilterInput.val("").trigger("input");
        });
    }
});

