// Interface messages only. Legal text, source notes and cache decisions stay in their owners.
export function loadFailureText(error){
 if(error?.message==='O arquivo não corresponde à edição publicada.')return 'O arquivo recebido não corresponde à edição publicada. Tente novamente; o texto não foi aberto.';
 if(['Coleção incompleta.','Índice incompleto.'].includes(error?.message))return 'Os dados recebidos estão incompletos. Tente carregar novamente.';
 return 'Não foi possível carregar este conteúdo. Tente novamente. Sem conexão, o acesso depende dos conteúdos já armazenados neste dispositivo.';
}
export function offlineStatusText(complete,online){
 return (online?'':'Você está offline. ')+(complete?'Biblioteca completa desta edição disponível offline.':'O acesso offline está limitado aos conteúdos armazenados neste dispositivo. A biblioteca completa ainda não foi preparada.');
}
