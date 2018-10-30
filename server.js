/*jshint esversion: 6 */
// TCP lib :
net = require('net');

// Un nouveau canal d'évènements
const EventEmitter = require('events');
class Chat extends EventEmitter{}
const ChatEvent = new Chat();

// Liste des clients (bon ok, en Node, on a aussi la fonction : server.getConnections() mais bon...)
var clients = [];

// Serveur TCP
net.createServer(function (socket) {

  // Evenement de nouvelle connexion
  ChatEvent.emit('connect', socket);

  // Quand on reçoit des données
  socket.on('data', function (data) {
    // On met les données dans ce socket sous "data"
    socket.data = data;
    // Evenement de nouveau message (on considère que la donnée reçue est un message)
    ChatEvent.emit('msg', socket);
  });

  // Quand quelqu'un se prend un timeout dans la tronche
  socket.on('timeout', function () {
    // Evenement de connexion en timeout
    ChatEvent.emit('timeout', socket);
  });

  // Quand une connexion est fermée
  socket.on('end', function () {
    // Evenement de fin de connexion
    ChatEvent.emit('end', socket);
  });

// Bon aller on écoute le port 5000, c'est bien 5000, j'aime bien 5000
}).listen(5000);

// Quand on chope une nouvelle connexion
ChatEvent.on('connect', (socket) => {
  // On donne un nom au socket, c'est pratique
  socket.name = socket.remoteAddress + ":" + socket.remotePort;
  // On ajoute un pseudo vide
  socket.pseudo = false;
  // On ajoute cette connexion à notre tableau des connexions active
  clients.push(socket);
  // On écrit le message de bienvenue
  socket.write("Welcome " + socket.name + "\r\nPlease set your pseudo with #pseudo=my_pseudo\r\n");
  // On prévient tout le monde que y'a un nouveau
  broadcast(socket.name + " joined the chat\r\n", socket);
  // On définit un tiemout pour éviter qu'un vilain de la NSA se pose en écoute dans notre super-chat !
  socket.setTimeout(2*60*60*1000); // en mili-secondes
});

// Quand on chope un nouveau message
ChatEvent.on('msg', (socket) => {
  var msg = socket.data.toString('ascii');
  if (msg.indexOf('#pseudo=') !== -1){
    // Changement de pseudo
    socket.pseudo = socket.data.toString('ascii').split('#pseudo=')[1].replace('\r','').replace('\n','');
    broadcast(socket.name + " has now pseudo "+socket.pseudo+'\r\n');
  }else{
    // On l'envoit à tout le monde
    if (socket.pseudo){
      broadcast(socket.pseudo + "> " + msg, socket);
    }else{
      broadcast(socket.name + "> " + msg, socket);
    }
  }
});

// Quand on chope un timeout
ChatEvent.on('timeout', (socket) => {
  // On vire le vilain espion de la NSA
  socket.end();
});

// Quand on chope une connexion qui se termine
ChatEvent.on('end', (socket) => {
  // On supprime du tableau des connexions actives
  clients.splice(clients.indexOf(socket), 1);
  // On prévient que untel s'est barré
  if (socket.pseudo){
    broadcast(socket.pseudo + " left the chat.\r\n");
  }else{
    broadcast(socket.name + " left the chat.\r\n");
  }
});

// Le fameux broadcast de la mort qui tue !
  function broadcast(message, sender) {
    // Pour nos clients actifs
    clients.forEach(function (client) {
      // Si c'est l'envoyeur, on ne lui renvoie pas
      if (client === sender) return;
      // Si c'est un autre, on lui envoie le message
      client.write(message);
    });
    // Et on log le message parce qu'on s'appelle Google et que même si un espion de la NSA n'est pas là, nous on aime les données, donc on copie au cas où !
    process.stdout.write(message)
  }

// On prévient dès que le serveur roule
console.log("Chat server running at port 5000\r\n");
