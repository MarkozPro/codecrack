// Vista previa de imágenes en el admin de Django
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todos los inputs de tipo file
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(function(input) {
        // Crear contenedor para la vista previa
        const previewContainer = document.createElement('div');
        previewContainer.style.marginTop = '10px';

        const previewImg = document.createElement('img');
        previewImg.style.maxWidth = '200px';
        previewImg.style.maxHeight = '200px';
        previewImg.style.borderRadius = '8px';
        previewImg.style.border = '1px solid #ddd';
        previewImg.style.padding = '5px';
        previewImg.style.display = 'none';

        previewContainer.appendChild(previewImg);
        input.parentNode.insertBefore(previewContainer, input.nextSibling);

        // Evento para mostrar la vista previa
        input.addEventListener('change', function(e) {
            const file = this.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    previewImg.src = event.target.result;
                    previewImg.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                previewImg.style.display = 'none';
            }
        });
    });
});