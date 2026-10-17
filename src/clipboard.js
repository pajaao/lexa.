export async function copyContent(text,button,message,toast){
 try{
  await navigator.clipboard.writeText(text);toast(message);
  const menu=button.closest('.article-copy');menu.open=false;menu.querySelector('summary').focus({preventScroll:true});
 }catch{
  const dialog=document.querySelector('#copy-dialog');
  const content=document.querySelector('#copy-content');content.value=text;
  dialog.showModal();content.focus();content.select();
 }
}
