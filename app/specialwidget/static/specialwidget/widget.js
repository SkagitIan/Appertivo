(function(){
    //import JQuery
    var newscript2 = document.createElement('script');
       newscript2.type = 'text/javascript';
       newscript2.async = true;
       newscript2.src = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.3/jquery.min.js';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(newscript2);
    //import Fontawesome
    var link1 = document.createElement("link");
    link1.type = "text/css";
    link1.rel = "stylesheet";
    link1.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.1/css/all.min.css';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(link1);
    //import CustomCSS
    var link2 = document.createElement("link");
    link2.type = "text/css";
    link2.rel = "stylesheet";
    link2.href = 'http://127.0.0.1:8000/static/specialwidget/widget.css';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(link2);
})();
function openForm() {
    document.getElementById("myForm").style.display = "block";
    const special_id = document.getElementById("special_id").value;
    const analytic_url = "http://127.0.0.1:8000/a/";
    console.log(analytic_url);
    $.ajax({
        type: "GET",
        dataType: 'data',
        crossDomain: true,
        url: analytic_url+special_id,
        success: function (data) {
            views = data.views
            document.getElementById("views").innerHTML = `
            ${views}
            `;
        },
        error: function(data)
        {
            console.log(data)
        }
    }); 

}  
function closeForm() {
    document.getElementById("myForm").style.display = "none";
    const special_id = document.getElementById("special_id").value;

}
//Function to signup users
function emailsignup(){
    
    const useremail = document.getElementById("useremail").value;
    const special_id = document.getElementById("special_id").value;
    var scriptName = document.getElementById('foodscriptone');
    var memberid = scriptName.getAttribute('memberid');
    if (/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(useremail))
    {
        
        signupurl = "http://127.0.0.1:8000/add_subscriber/"+memberid+"/"+useremail+"/"+special_id;
        $.ajax({
            type: "GET",
            dataType: 'html',
            crossDomain: true,
            url: signupurl,
            success: function (data) {
                document.getElementById("form-container").innerHTML = `${data}`;
            },
            error: function(data)
            {
                console.log(data);
            }
        }); 
    }
    else{
        document.getElementById("form-container").innerHTML = "Please enter a valid email address!";
    }
}
window.onload = function(){
    var scriptName = document.getElementById('foodscriptone');
    var memberid = scriptName.getAttribute('memberid');
    const foodurl = "http://127.0.0.1:8000/dashboard/iframe/";
    console.log(foodurl);
    $.ajax({
        type: "GET",
        dataType: 'html',
        crossDomain: true,
        url: foodurl+memberid,
        success: function (html) {

            document.getElementById("fooddiv").innerHTML = `
            <button class="open-button text-white text-center" onclick="openForm()" style="z-index: 10;font-size:1em;"><i class="fas fa-utensils"></i></button>
            <div class="chat-popup" id="myForm" style="z-index: 25;overflow:hidden;">
          
            ${html}
            </div>
            `;
        },
        error: function(html)
        {
            console.log(html)
        }
    }); 
}