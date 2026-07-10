# 📐 Spec: Critérios de Prontidão para Softwares de Rede (Network Production Readiness)

Esta especificação dita as diretrizes e os limites arquiteturais que qualquer código focado em redes escrito em JavaScript por este agente precisa cumprir para garantir estabilidade operacional.

## 1. Eficiência do Event Loop & Conexões
* **Non-Blocking IO:** É proibido o uso de qualquer método síncrono do módulo `fs` ou chamadas bloqueantes em rotas de tratamento de dados de rede.
* **Pool de Conexões:** Clientes HTTP/HTTPS criados devem reutilizar conexões utilizando um `http.Agent` ou `https.Agent` configurado com `keepAlive: true` e `maxSockets` controlado.

## 2. Padrões de Segurança de Rede
* **Sanitização de Input:** Inputs do usuário que passem IPs, subredes (CIDR) ou DNS devem ser validados usando expressões regulares rígidas ou o método nativo `net.isIP()` antes de inicializar o socket.
* **Privilégios Mínimos:** O script não deve rodar permanentemente como `root`. Se precisar abrir uma porta restrita (abaixo de 1024), deve usar um proxy reverso (Nginx) ou fazer o downgrade do processo usando `process.setuid()` logo após a abertura do socket.

## 3. Telemetria e Monitoramento de Conexão
* **Keep-Alive Application-Level:** Para conexões persistentes de longa duração (como WebSockets), o código deve implementar uma rotina de ping/pong ativa para identificar desconexões em nível de aplicação antes do socket do SO falhar.
* **Tratamento de Desconexões Abruptas:** O fechamento de um canal de rede (`close` ou `end`) deve liberar imediatamente todos os recursos, limpar listeners associados (`removeAllListeners`) e interromper temporizadores de timeout ativos para evitar vazamento de memória (*memory leaks*).

## 🏁 Checklist de Aceitação (Definition of Done)
- [ ] O tratamento de erros cobre cenários de `ECONNREFUSED`, `ETIMEDOUT` e `EHOSTUNREACH`.
- [ ] Todos os streams implementados usam `stream.pipeline` ou tratam o evento de erro para prevenir vazamentos.
- [ ] A aplicação passa no teste de estresse de 100 conexões simultâneas sem travar o loop de eventos por mais de 50ms.
- [ ] Strings de conexão e credenciais de servidores (SSH/API tokens) são lidas exclusivamente de variáveis de ambiente (`process.env`).