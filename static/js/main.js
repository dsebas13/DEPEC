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
      if(!confirm('Esta seguro que desea postularse a esta busqueda?')){
        e.preventDefault();
      }
    });
  })
}