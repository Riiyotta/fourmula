document.addEventListener("DOMContentLoaded", function(){
  const items=document.querySelectorAll(".faq__item");
  items.forEach(item=>{
    const title=item.querySelector(".faq__item-title");
    const content=item.querySelector(".faq__content");
    const icon=item.querySelector(".faq__icon");
    content.style.display="none";
    content.style.height="0px";
    content.style.opacity="0";
    icon.textContent="+";
    title.addEventListener("click",()=>{
      const isOpen=item.classList.contains("active");
      items.forEach(other=>{
        if(other!==item){
          other.classList.remove("active");
          const oc=other.querySelector(".faq__content");
          const oi=other.querySelector(".faq__icon");
          oc.style.height="0px";
          oc.style.opacity="0";
          setTimeout(()=>{oc.style.display="none"},350);
          oi.textContent="+";
        }
      });
      if(!isOpen){
        item.classList.add("active");
        content.style.display="block";
        void content.offsetWidth;
        content.style.height=content.scrollHeight+"px";
        content.style.opacity="1";
        icon.textContent="-";
      }else{
        item.classList.remove("active");
        content.style.height="0px";
        content.style.opacity="0";
        setTimeout(()=>{content.style.display="none"},350);
        icon.textContent="+";
      }
    });
  });
});