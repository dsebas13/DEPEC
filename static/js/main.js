const btnDelete= document.querySelectorAll('.btn-delete');
if(btnDelete) {
  const btnArray = Array.from(btnDelete);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('Esta seguro que desea borrar este elemento?')){
        e.preventDefault();
      }
    });
  })
}

const btnAdd= document.querySelectorAll('.btn-add');
if(btnAdd) {
  const btnArray = Array.from(btnAdd);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('Esta seguro que desea postularse a esta búsqueda?')){
        e.preventDefault();
      }
    });
  })
}

const btnlock= document.querySelectorAll('.btn-lock');
if(btnlock) {
  const btnArray = Array.from(btnlock);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('Esta seguro que desea cerrar esta busqueda, este proceso es irreversible?')){
        e.preventDefault();
      }
    });
  })
}

const btnpostu= document.querySelectorAll('.btn-postu');
if(btnpostu) {
  const btnArray = Array.from(btnpostu);
  btnArray.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      if(!confirm('Esta seguro que desea inactivar su postulación?')){
        e.preventDefault();
      }
    });
  })
}