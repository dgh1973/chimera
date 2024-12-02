function ChangeColor(tableRow, color, highLight)
{
    if (highLight)
    {
          tableRow.style.backgroundColor = color;
    }
    else
    {
          tableRow.style.backgroundColor = color;
    }
}

function DoNav(theUrl)
{
    document.location.href = theUrl;
}

/*
function displayRow(id)
{
    var row = document.getElementById("outputRow" + id);
    if (row.style.display == 'table-row')
    {
        row.style.display = 'none';
    }
    else
    {
        row.style.display = 'table-row';
    }
}

*/
function MoveElement(id, pos1, pos2)
{
    if (document.getElementById(id).style.left == pos1)
    {
        document.getElementById(id).style.left = pos2;
    }
    else
    {
        document.getElementById(id).style.left = pos1;
    }
}
