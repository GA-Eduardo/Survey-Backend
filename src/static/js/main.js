window.addEventListener('DOMContentLoaded', (event) => {
  console.log('DOM fully loaded and parsed');
  history.pushState(null, null, location.href);
  history.back();
  history.forward();
  window.onpopstate = function () {
    history.go(1);
  };
});
function mouseOver(id) {
  document.getElementById(id).style.color = 'yellow';
  document.getElementById(id).style.background = 'grey';
}

function mouseOut(id) {
  document.getElementById(id).style.color = 'whitesmoke';
  document.getElementById(id).style.background = '#3b404e';
}

function selectedFile() {
  var archivoSeleccionado = document.getElementById('fileupload');
  var file = archivoSeleccionado.files[0];
  if (file) {
    var fileSize = 0;
    if (file.size > 1048576)
      fileSize =
        (Math.round((file.size * 100) / 1048576) / 100).toString() + ' MB';
    else
      fileSize =
        (Math.round((file.size * 100) / 1024) / 100).toString() + ' Kb';

    var divfileSize = document.getElementById('fileSize');
    var divfileType = document.getElementById('fileType');
    divfileSize.innerHTML = 'Tamaño: ' + fileSize;
    divfileType.innerHTML = 'Tipo: ' + file.type;
    document.getElementById('subir').style.display = 'block';
  } else {
    document.getElementById('subir').style.display = 'none';
  }
}

async function uploadFile() {
  document.getElementById('subir').style.display = 'none';
  alert('You have successfully upload the file!');
}
