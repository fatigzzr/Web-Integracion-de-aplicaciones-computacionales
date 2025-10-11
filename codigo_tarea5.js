// JavaScript para los menús desplegables de codigo_tarea5.html

document.addEventListener('DOMContentLoaded', function() {
    var coll = document.getElementsByClassName("collapsible");
    var i;

    for (i = 0; i < coll.length; i++) {
        coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            
            if (this.classList.contains("active")) {
                content.classList.add("active");
            } else {
                content.classList.remove("active");
            }
        });
    }
});
