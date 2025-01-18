document.addEventListener('DOMContentLoaded', function () {
    $('#editModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var filePath = button.data('filepath');
        var modal = $(this);
        modal.find('.modal-body #edit_file_path').val(filePath);
    });

    $('#renameModal').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget);
        var filePath = button.data('filepath');
        var modal = $(this);
        modal.find('.modal-body #rename_file_path').val(filePath);
    });
});
