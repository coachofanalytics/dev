const days = cookieadmin_policy.cookieadmin_days;

if(typeof cookieadmin_is_consent === 'undefined'){
	window.cookieadmin_is_consent = {};
}
var cookieadmin_allcookies = cookieadmin_policy.categorized_cookies;
//setInterval(cookieadmin_categorize_cookies, 5000);

function cookieadmin_is_obj(consentObj){
	return (Object.keys(consentObj).length !== 0);
}


// function cookieadmin_cookie_interceptor(){
	
	const originalCookieDescriptor =
    Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
    Object.getOwnPropertyDescriptor(document, 'cookie');
	var allowed_cookies = '';

	// Override document.cookie to intercept cookie setting.
	Object.defineProperty(document, 'cookie', {
		configurable: true,
		enumerable: true,
		get: function(){
			return originalCookieDescriptor.get.call(document);
		},
		set: function(val){
			if (!val) return false;
			
			splited_val = val.split("=");
			val_name = splited_val[0].trim();
			
			if(splited_val[1].trim().startsWith("deleted;")) return false;
			
			rm_val = val_name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
			
			if(val_name === "cookieadmin_consent"){
				return originalCookieDescriptor.set.call(document, val);
			}
			
			if(cookieadmin_is_obj(cookieadmin_is_consent) && (val_name in cookieadmin_allcookies) ){
					
				if(!!cookieadmin_is_consent.action.reject){
					return originalCookieDescriptor.set.call(document, rm_val);
				}					
				else if(!!cookieadmin_is_consent.action.accept){
					return originalCookieDescriptor.set.call(document, val);
				}
				else if(!!cookieadmin_allcookies[val_name].category){
					
					if(cookieadmin_is_consent.action[cookieadmin_allcookies[val_name].category.toLowerCase()]){
						return originalCookieDescriptor.set.call(document, val);
					}
					else{
						return originalCookieDescriptor.set.call(document, rm_val);
					}
					return true;
				}					
				
			}else{
				(cookieadmin_allcookies[val_name] = cookieadmin_allcookies[val_name] || {}).string = val.trim();
				return false;
			}
			
		}
	});
// }
// cookieadmin_cookie_interceptor();


function cookieadmin_is_cookie(name){
	
	if(!document.cookie) return false;
	
	let coki = document.cookie.split(";") ;
	
	if(name == "all"){
		return coki ? coki : [];
	}
	let nam = name + "=";
	
	for(let i=0; i < coki.length; i++){
		if(coki[i].trim().indexOf(nam) == 0){
				return coki[i].trim();
		}
	}
	
	return false;
}

function cookieadmin_check_consent(){
	
	if(cookieadmin_cookie = cookieadmin_is_cookie("cookieadmin_consent")){
		cookieadmin_cookie = JSON.parse(cookieadmin_cookie.split("=")[1]);
		if(!!cookieadmin_cookie.consent){
			cookieadmin_is_consent.consent = cookieadmin_cookie.consent;
			delete cookieadmin_cookie.consent;
		}
		
		cookieadmin_is_consent.action = cookieadmin_cookie;
	}
}
cookieadmin_check_consent();

function cookieadmin_restore_cookies(update) {
    
	var cookieadmin_accepted_categories = [];
	
	if(update.accept && update.accept == "true"){
		
		document.querySelectorAll(".cookieadmin_toggle").forEach(function(e){
			key = e.children[0].id;
			if (key.includes("cookieadmin-")) {
				key = key.replace("cookieadmin-", "");
				cookieadmin_accepted_categories.push(key);
			}
		});
		
	}else if(update.reject && update.reject == "true"){
		return true;
	}else{
		for (const [key, value] of Object.entries(update)) {
			if(key != "consent"){
				cookieadmin_accepted_categories.push(key);
			}
		}
	}
	
	
  	for(cookie in cookieadmin_allcookies){
  		document.cookie = cookie.string;
  	};
	
    cookieadmin_accepted_categories.forEach(function(category) {
		
        document.querySelectorAll(
            'script[type="text/plain"][data-cookieadmin-category="' + category + '"]'
        ).forEach(function(el) {
            const newScript = document.createElement('script');

            // Copy attributes
            if (el.src) {
                newScript.src = el.src;
            } else {
                newScript.text = el.textContent;
            }

            if (el.defer) newScript.defer = true;
            if (el.async) newScript.async = true;

            // Copy other attributes if needed
            ['id', 'class', 'data-name'].forEach(attr => {
                if (el.hasAttribute(attr)) {
                    newScript.setAttribute(attr, el.getAttribute(attr));
                }
            });

            el.parentNode.replaceChild(newScript, el);
        });
    });
}

function cookieadmin_set_cookie(name, value, days = 365, domain = "") {
  if (!name || !value) return false;

  const date = new Date();
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000); // default 1 year

  let cookieString = `${encodeURIComponent(name)}=${JSON.stringify(value)};`;
  cookieString += ` expires=${date.toUTCString()};`;
  cookieString += ` path=${cookieadmin_policy.base_path};`;
  cookieString += ` SameSite=Lax;`;
  if(cookieadmin_policy.is_ssl || window.location.protocol === 'https:'){
	  cookieString += ` Secure;`;
  }

  // Add domain if explicitly passed
  if (domain) {
    cookieString += ` domain=${domain};`;
  }

  document.cookie = cookieString;
  return true;
}

//Populates modal with consent if selected
function cookieadmin_populate_preference(){
	
	consent = cookieadmin_is_consent.action;
	
	if(!!consent){
		
		if(consent.accept){
			document.querySelectorAll(".cookieadmin_toggle").forEach(function(e){
				e.children[0].checked = true;
			});
		}
		else if(consent.reject){
			document.querySelectorAll(".cookieadmin_toggle").forEach(function(e){
				e.children[0].checked = false;
			});
		}
		else{
			for(btn in consent){
				if(btn_ele = document.querySelector("#cookieadmin-" + btn)){
					btn_ele.checked = true;
				}
			}
		}
	}
	
	cookieadmin_shown = (typeof cookieadmin_shown !== "undefined") ? cookieadmin_shown : [];
	
	if(cookieadmin_allcookies){
		
		cookieadmin_filtrd = Object.keys(cookieadmin_allcookies).filter(e => !cookieadmin_shown.includes(e));
		
		for(c_info of cookieadmin_filtrd){
			
			if(e = document.querySelector(".cookieadmin-" + cookieadmin_allcookies[c_info].category?.toLowerCase())){
				e.innerHTML = (e.innerHTML == 'None') ?  '' : e.innerHTML;
				
				exp = cookieadmin_policy.lang.session;
					
				if(!!cookieadmin_allcookies[c_info].expires){
					exp = Math.round((cookieadmin_allcookies[c_info].expires - Date.now())/86400);
					if(exp < 1 && !!res['Max-Age']){
						exp = res['Max-Age'];
					}else{
						exp = cookieadmin_policy.lang.session;
					}
				}
				
				e.innerHTML += '<div class="cookieadmin-cookie-card"> <div class="cookieadmin-cookie-header"> <strong class="cookieadmin-cookie-name">'+ c_info.replace(/_+$/, "") +'</strong> <span class="cookieadmin-cookie-duration"><b>'+ cookieadmin_policy.lang.duration +':</b> '+ exp +'</span> </div> <p class="cookieadmin-cookie-description">'+ cookieadmin_allcookies[c_info].description +'</p> <div class="cookieadmin-cookie-tags"> ' + (cookieadmin_allcookies[c_info].platform ? '<span class="cookieadmin-tag">' + cookieadmin_allcookies[c_info].platform + '</span>' : "") + ' </div> </div>';
			}
			cookieadmin_shown.push(c_info);
		}
	}
		
}

function cookieadmin_toggle_overlay(){
	
	if(window.getComputedStyle(document.getElementsByClassName("cookieadmin_modal_overlay")[0]).display == "none"){
		document.getElementsByClassName("cookieadmin_modal_overlay")[0].style.display = "block";
	}else{
		document.getElementsByClassName("cookieadmin_modal_overlay")[0].style.display = "none";
	}
	
}

function cookieadmin_categorize_cookies(){
	
	if(!cookieadmin_allcookies){
		return;
	}
	
	var cookieadmin_chk_cookies = {};
	var cookieadmin_consent_chng = [];
	
	for(a_cookie in cookieadmin_allcookies){
		if(!cookieadmin_allcookies[a_cookie].category){
			cookieadmin_chk_cookies[a_cookie] = cookieadmin_allcookies[a_cookie];
		}else if(cookieadmin_is_consent.old_action !== cookieadmin_is_consent.action && a_cookie !== "cookieadmin_consent"){
			document.cookie = cookieadmin_allcookies[a_cookie].string;
		}
	}
	
	if(!cookieadmin_is_obj(cookieadmin_chk_cookies)){
		return;
	}
	
	/* const xhttp2 = new XMLHttpRequest();
	
	var data = 'action=cookieadmin_ajax_handler&cookieadmin_act=categorize_cookies&cookieadmin_security=' + cookieadmin_policy.nonce + "&cookieadmin_cookies=" + JSON.stringify(cookieadmin_chk_cookies);
	
	xhttp2.onload = function() {
		parsd = JSON.parse(this.responseText);
		
		if(parsd.success){
			cookies = parsd.data;
			for(coki in cookies){
				cookieadmin_chk_cookies[coki].name = coki;
				if(cookies[coki].category === "un_c"){
					cookieadmin_chk_cookies[coki].source = "unknown";
					cookieadmin_chk_cookies[coki].description = "unknown";
				}
				cookieadmin_allcookies[coki] = cookieadmin_chk_cookies[coki];
				document.cookie = cookieadmin_chk_cookies[coki].string;
			}
		}
	}
	
	xhttp2.open("POST", cookieadmin_policy.ajax_url, true);
	xhttp2.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
	xhttp2.send(data); */
}


document.addEventListener("DOMContentLoaded", function() {
	
	var cookieadmin_show_reconsent = 0;
	if(cookieadmin_policy.is_pro != 0 && cookieadmin_pro_vars.reconsent != 0){
		var cookieadmin_show_reconsent = 1;
	}

	//Create overlay
	var cookieadmin_ovrlay =  document.createElement("div");
	cookieadmin_ovrlay.className = "cookieadmin_modal_overlay";
	document.body.appendChild(cookieadmin_ovrlay);
	
	//Show notice or re-consent icon as needed
	if(!cookieadmin_is_obj(cookieadmin_is_consent)){
		
		if(cookieadmin_policy.cookieadmin_layout !== "popup"){
			document.getElementsByClassName("cookieadmin_law_container")[0].style.display = "block";
		}else{
			cookieadmin_toggle_overlay();
			document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "flex";
		}
		
		/* //block cookie scripts
		var cookieadmin_blockedScripts = [
			'https://www.google-analytics.com/analytics.js',
			'https://connect.facebook.net/en_US/fbevents.js',
			'https://www.youtube.com/iframe_api'
		];
		
		cookieadmin_blockedScripts.forEach(function(scriptUrl) {
			var scriptTag = document.querySelector(`script[src='${scriptUrl}']`);
			if (scriptTag) {
				scriptTag.remove();  // Remove script if already loaded
			}
		}); */
		
	}else if(cookieadmin_show_reconsent){
		document.getElementsByClassName("cookieadmin_re_consent")[0].style.display = "block";	
		
	}
	
	//Edit Notice and Modal contents
	document.getElementsByClassName("cookieadmin_reconsent_img")[0].src = cookieadmin_policy.plugin_url + "/assets/images/cookieadmin_icon.svg";

	cookieadmin_populate_preference();

	for(data in cookieadmin_policy){

		typ = 0;
		if(data.includes("_bg_color")){
			d_ele = data.replace("_bg_color", "");
			typ = 1;
		}else if(data.includes("_border_color")){
			d_ele = data.replace("_border_color", "");
			typ = 2;
		}else if(data.includes("_color")){
			d_ele = data.replace("_color", "");
			typ = 3;
		}else{
			d_ele = data;
		}
		
		d_eles = [];
		if(document.getElementById(d_ele)){
			d_eles = [document.getElementById(d_ele)];
		}
		if(document.getElementsByClassName(d_ele).length){
			d_eles = (document.getElementsByClassName(d_ele).length > 1) ? document.getElementsByClassName(d_ele) : [document.getElementsByClassName(d_ele)[0]];
		}
		
		if(!!d_eles){
			i = 0;
			while(i < d_eles.length){
				d_ele = d_eles[i];
				if(typ == 3){
					d_ele.style.color = cookieadmin_policy[data];
				}else if(typ == 2){
					d_ele.style.borderColor = cookieadmin_policy[data];
				}else if(typ == 1){
					d_ele.style.backgroundColor = cookieadmin_policy[data];
				}else{
					d_ele.innerHTML = cookieadmin_policy[data];
				}
				i++;
			}
		}		
	}

	//Add layout as class
	if(!!cookieadmin_policy.cookieadmin_position){
		cookieadmin_policy.cookieadmin_position.split("_").forEach(function(clas){
			clas = "cookieadmin_" + clas;
			document.getElementsByClassName("cookieadmin_law_container")[0].classList.add(clas);
		});
	}

	// Change consent layout dynamically
	document.getElementsByClassName("cookieadmin_law_container")[0].classList.add("cookieadmin_" + cookieadmin_policy.cookieadmin_layout);

	// Change Modal layout dynamically
	document.getElementsByClassName("cookieadmin_cookie_modal")[0].classList.add("cookieadmin_" + cookieadmin_policy.cookieadmin_modal);

	/*if(cookieadmin_policy.layout == "footer"){
		
	}*/

	if(cookieadmin_policy.cookieadmin_modal == "side"){
		document.getElementsByClassName("cookieadmin_modal_footer")[0].style.flexDirection = "column";
	}
		
	// Remove modal close Button
	if(cookieadmin_policy.cookieadmin_layout == "popup"){
		document.getElementsByClassName("cookieadmin_close_pref")[0].style.display = "none";
	}

	//show preference modal
	cookieadmin_show_modal_elemnts = document.querySelectorAll(".cookieadmin_re_consent, .cookieadmin_customize_btn");
	cookieadmin_show_modal_elemnts.forEach(function(e){
		
		e.addEventListener("click", function(e){
			
			/*cookieadmin_is_cookie("all").forEach(function(e){
				c_name = e.split("=")[0].trim();
				if(!!cookieadmin_allcookies[c_name]){
					console.log(JSON.stringify(cookieadmin_allcookies[c_name]));
				}
			});*/
			
			cookieadmin_toggle_overlay();
			document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "flex";
			document.getElementsByClassName("cookieadmin_re_consent")[0].style.display = "none";
			document.getElementsByClassName("cookieadmin_law_container")[0].style.display = "none";
			
			if(cookieadmin_policy["cookieadmin_modal"] == "side"){
				document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "grid";
			}
			
			if(e.target.className == "cookieadmin_re_consent"){
				document.getElementsByClassName("cookieadmin_close_pref")[0].id = "cookieadmin_re_consent";
			}else{
				document.getElementsByClassName("cookieadmin_close_pref")[0].id = "cookieadmin_law_container";
			}
		});
	});
	
	//Save preference
	document.querySelector(".cookieadmin_save_btn").addEventListener("click", function(){
		
		document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "none";
		if(cookieadmin_show_reconsent){
			document.getElementsByClassName("cookieadmin_re_consent")[0].style.display = "block";
		}
		
		var prefer = {};

		document.querySelectorAll(".cookieadmin_toggle").forEach(function(e){
			if(!!e.children[0].checked){
				prefer[e.children[0].id.replace("cookieadmin-","")] = 'true';
			}
		});
		
		if(Object.keys(prefer).length !== 0){
			if(Object.keys(prefer).length === 3){
				document.querySelectorAll(".cookieadmin_accept_btn")[1].click();
				return;
			}
		}else{
			document.querySelectorAll(".cookieadmin_reject_btn")[1].click();
			return;
		}
		
		cookieadmin_toggle_overlay();

		cookieadmin_set_consent(prefer, days);
	});


	//Accept or reject all cookies
	cookieadmin_save_all_cookie_elemnts = document.querySelectorAll(".cookieadmin_accept_btn, .cookieadmin_reject_btn");

	cookieadmin_save_all_cookie_elemnts.forEach(function(e){
		
		e.addEventListener("click", function(){
			// console.log(e);

			document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "none";
			document.getElementsByClassName("cookieadmin_law_container")[0].style.display = "none";
			if(cookieadmin_show_reconsent){
				document.getElementsByClassName("cookieadmin_re_consent")[0].style.display = "block";
			}
			
			if(e.id.includes("modal")){
				cookieadmin_toggle_overlay();
			}
			
			var prefer2 = e.classList.contains("cookieadmin_reject_btn") ? {reject: "true"} : {accept: "true"};
			
			cookieadmin_set_consent(prefer2, days);
		});
	});
	
	//showmore modal btn
	document.getElementsByClassName("cookieadmin_showmore")[0]?.addEventListener("click", function(){
		
		var cur_height = document.getElementsByClassName("cookieadmin_preference")[0].style.height;
		
		if(!cur_height){
			document.getElementsByClassName("cookieadmin_preference")[0].style.height = "auto";
			this.innerHTML = cookieadmin_policy.lang.show_less;
		}else{
			document.getElementsByClassName("cookieadmin_preference")[0].style.height = "";
			this.innerHTML = cookieadmin_policy.lang.show_more;
		}
	});


	document.querySelectorAll(".cookieadmin_show_pref_cookies").forEach(function(e){
		e.addEventListener("click", function(el){
			
			var tgt = el.target.id;
			tgt = tgt.replace(/-container$/, "");
			
			if(el.target.classList.contains("dwn")){
				el.target.innerHTML = "&#9658;";
				el.target.classList.remove("dwn");
				document.querySelector("."+tgt).style.display = "none";
			}else{
				el.target.innerHTML = "&#9660;";
				el.target.classList.add("dwn");
				document.querySelector("."+tgt).style.display = "block";
			}
		});
	});

	document.getElementsByClassName("cookieadmin_close_pref")[0].addEventListener("click", function(e){
		document.getElementsByClassName("cookieadmin_cookie_modal")[0].style.display = "none";
		cookieadmin_toggle_overlay();
		if(!cookieadmin_is_obj(cookieadmin_is_consent)){
			document.getElementsByClassName("cookieadmin_law_container")[0].style.display = "block";
		}else if(cookieadmin_show_reconsent){
			document.getElementsByClassName("cookieadmin_re_consent")[0].style.display = "block";
		}
	});
	
});

function cookieadmin_set_consent(prefrenc, days){
	
	if (typeof cookieadmin_pro_set_consent === "function") {
		return cookieadmin_pro_set_consent(prefrenc, days);
	}else{
		return cookieadmin_save_consent_cookie(prefrenc, days);
	}
}

function cookieadmin_save_consent_cookie(prefrenc, days, consent_id){
	
	var cookieadmin_consent = prefrenc;
		
	if(consent_id){
		cookieadmin_is_consent.consent = consent_id;
		cookieadmin_consent['consent'] = consent_id;
	}
	
	if(!cookieadmin_is_consent.consent){
		cookieadmin_is_consent.consent = "";
	}
	
	cookieadmin_is_consent["old_action"] = cookieadmin_is_consent.action ? cookieadmin_is_consent.action : {};
	cookieadmin_is_consent.action = prefrenc;
	cookieadmin_populate_preference();
	cookieadmin_set_cookie('cookieadmin_consent', cookieadmin_consent, days);
	
	if (typeof cookieadmin_update_gcm === "function") {
		cookieadmin_update_gcm(1);
	}
	
	if(!!cookieadmin_policy.reload_on_consent){
		location.reload();
	}else{
		cookieadmin_restore_cookies(prefrenc);
	}
}

