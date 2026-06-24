// Cloudflare Worker - EVE Online OAuth Proxy
const CLIENT_ID = "7abe9f4cc09d46638138891fc9b077f5";
const REDIRECT_URI = "https://eve-oauth-proxy.sergrudzik.workers.dev/callback";
const CCP_AUTH_URL="https://login.eveonline.com/v2/oauth/authorize";
const CCP_TOKEN_URL="https://login.eveonline.com/v2/oauth/token";
const CCP_VERIFY_URL = 'https://login.eveonline.com/oauth/verify';

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    const h = {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type","Content-Type":"application/json"};
    if (request.method === "OPTIONS") return new Response(null, {status:204,headers:h});
    try {
      if (path === "/" && request.method === "GET")
        return new Response(JSON.stringify({status:"ok",name:"eve-online-oauth-proxy"}),{headers:h});
      if (path === "/exchange" && request.method === "POST") {
        const b=await request.json();
        if (!b.code||!b.code_verifier) return new Response(JSON.stringify({error:"Missing code or code_verifier"}),{status:400,headers:h});
        const r=await fetch(CCP_TOKEN_URL,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({grant_type:"authorization_code",code:b.code,code_verifier:b.code_verifier,redirect_uri:REDIRECT_URI,client_id:CLIENT_ID,client_secret:CLIENT_SECRET}).toString()});
        const td=await r.json();
        if(!r.ok) return new Response(JSON.stringify({error:"exchange_failed"}),{status:400,headers:h});
        const vr=await fetch(CCP_VERIFY_URL,{headers:{Authorization:"Bearer "+td.access_token}});
        const vd=await vr.json();
        if(!vr.ok) return new Response(JSON.stringify({error:"verify_failed"}),{status:400,headers:h});
        return new Response(JSON.stringify({access_token:td.access_token,refresh_token:td.refresh_token,character_id:vd.CharacterID,character_name:vd.CharacterName}),{headers:h});
      }
      if (path === "/refresh" && request.method === "POST") {
        const b=await request.json();
        if (!b.refresh_token) return new Response(JSON.stringify({error:"Missing refresh_token"}),{status:400,headers:h});
        const r=await fetch(CCP_TOKEN_URL,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({grant_type:"refresh_token",refresh_token:b.refresh_token,client_id:CLIENT_ID,client_secret:CLIENT_SECRET}).toString()});
        const td=await r.json();
        if(!r.ok) return new Response(JSON.stringify({error:"refresh_failed"}),{status:400,headers:h});
        return new Response(JSON.stringify({access_token:td.access_token,refresh_token:td.refresh_token||b.refresh_token}),{headers:h});
      }
      if (path === "/callback") {
        const err=url.searchParams.get("error");
        if(err) return new Response("<html><body><h1>Auth Failed</h1></body></html>",{headers:{"Content-Type":"text/html"}});
        const code=url.searchParams.get("code");
        if(code) return new Response("<!DOCTYPE html><html><body style=\"font-family:sans-serif;text-align:center;padding:40px;background:#101010;color:#f4f7f8\"><h1 style=\"color:#8dc169\">Auth OK!</h1><p>Return to Home Assistant.</p></body></html>",{headers:{"Content-Type":"text/html;charset=utf-8"}});
        return new Response("<html><body><h1>No code</h1></body></html>",{headers:{"Content-Type":"text/html"}});
      }
      return new Response(JSON.stringify({error:"Not found"}),{status:404,headers:h});
    } catch(err) {return new Response(JSON.stringify({error:"Internal error",details:err.message}),{status:500,headers:h});}
  },
};