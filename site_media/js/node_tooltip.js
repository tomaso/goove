var mousex = 0;
var mousey = 0;

function getMouseXY(e) // works on IE6,FF,Moz,Opera7
{
  if (!e) e = window.event; // works on IE, but not NS (we rely on NS passing us the event)

  if (e)
  {
    if (e.pageX || e.pageY)
    { // this doesn't work on IE6!! (works on FF,Moz,Opera7)
      mousex = e.pageX;
      mousey = e.pageY;
    }
    else if (e.clientX || e.clientY)
    { // works on IE6,FF,Moz,Opera7
      mousex = e.clientX + document.body.scrollLeft;
      mousey = e.clientY + document.body.scrollTop;
    }
  }
}

function show_node_tt(e,o) {
  if (!e) e = window.event
  getMouseXY(e);

  var obj = document.getElementById("node_tt_"+o.id);
  var st = Math.max(document.body.scrollTop,document.documentElement.scrolltop);

  var leftPos = mousex + 20;
  var topPos = mousey + 20;
  obj.style.left = leftPos + 'px';
  obj.style.top = topPos + 'px';
  obj.style.display="block";
}


function hide_node_tt(o) {
  document.getElementById("node_tt_"+o.id).style.display="none";
}

