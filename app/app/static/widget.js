(function(){
    //import JQuery
    var newscript2 = document.createElement('script');
       newscript2.type = 'text/javascript';
       newscript2.async = true;
       newscript2.src = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min.js';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(newscript2);
    //import Fontawesome
    var link1 = document.createElement("link");
    link1.type = "text/css";
    link1.rel = "stylesheet";
    link1.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.13.0/css/all.min.css';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(link1);
    //import CustomCSS
    var link2 = document.createElement("link");
    link2.type = "text/css";
    link2.rel = "stylesheet";
    link2.href = '127.0.0.1/static/media/widget.css';
    (document.getElementsByTagName('head')[0]||document.getElementsByTagName('body')[0]).appendChild(link2);
})();
function openForm() {
    document.getElementById("myForm").style.display = "block";
}  
function closeForm() {
    document.getElementById("myForm").style.display = "none";

}
//Function to signup users
function emailsignup(){
    document.getElementById("errorifany").innerHTML = "";
    document.getElementById("success").innerHTML = "";
    const useremail = document.getElementById("userfoodemail").value;
    var scriptName = document.getElementById('foodscriptone');
    var memberid = scriptName.getAttribute('memberid');
    if (/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/.test(useremail))
    {
        document.getElementById("errorifany").innerHTML = "";
        signupurl = "https://appertivo.com/ss?id="+memberid+"&email="+useremail;
        $.ajax({
            type: "GET",
            dataType: 'json',
            crossDomain: true,
            url: signupurl,
            success: function (data) {
                document.getElementById("success").innerHTML = "Successfully registered!";
            },
            error: function(data)
            {
                console.log(data);
            }
        }); 
    }
    else{
        document.getElementById("errorifany").innerHTML = "Please enter a valid email address!";
    }
} 
window.onload = function(){
    var scriptName = document.getElementById('foodscriptone');
    var memberid = scriptName.getAttribute('memberid');
    const foodurl = "127.0.0.1:8000/dashboard/widget/iframe/";
    console.log(foodurl);
    var title = "Title";
    var image = "MoonCake.jpg";
    $.ajax({
        type: "GET",
        dataType: 'json',
        crossDomain: true,
        url: foodurl+memberid,
        success: function (data) {
            title = data.title;
            image = data.thumbnail;
            date_ending = data.end_date;
            document.getElementById("fooddiv").innerHTML = `
                <button class="open-button text-white text-center" onclick="openForm()" style="z-index: 10;font-size:2em;"><i class="fas fa-utensils"></i></button>
                <ul class="callouts" id="callouts">
                <li class="callouts--right text-dark"><i class="fas fa-smile" style="color:#f58f29;"></i> Would you like to hear about our specials?</li></ul>
              
                <div class="chat-popup" id="myForm" style="z-index: 25;overflow:hidden;">

                    <form action="javascript:void(0);" class="form-container">
                        <p style="text-align: right;margin-bottom: -10px;cursor: pointer;"  onclick="closeForm()"><i style="color: #333;"class="fas fa-window-close"></i></p>
                        <h2 style="text-align: center;color:#fff;margin-top:0;font-weight:100;">Today's Special</h2>
                        <hr>
                        <p style="color:#fff;font-weight:100;"><center><strong>Ends:</strong> ${date_ending}</center></p>
                        <p style="border:2px solid #eee; text-align: center;margin-bottom: 8px;overflow:hidden;"><img src="${image}" id="gify" alt="food" class="img-fluid" style="border:1px solid #eee;"></p>
                        <p class="" style="color:#fff;font-size:1.25em;font-weight:100;text-align: center;margin-top:0px;">${title}</p>
                        <div style="width: 250px;margin: 0 auto;padding-bottom:10px;">

                            <p id="errorifany" style="color:red"></p>
                            <p id="success" style="color:green"></p>
                            <input type="email" style="width: 100%;height: 30px;padding:5px;" id="userfoodemail" placeholder="Enter Your Email">
                            <button type="button" class="border btn btn-sm cancel" style="background-color: #9677cf;border:1px solid #eee; margin-top: 5px;margin-bottom:10px;" onclick="emailsignup();">Get specials emailed to you</button><br/>
                            <small class="text-light"><center>Powered by <a href="https://appertivo.com" style="color:#fff;"><strong>Appertivo</strong></a></center></small>
                        </div>
                    </form>
                </div>
                `;
        },
        error: function(data)
        {
            console.log(data)
        }
    }); 
}