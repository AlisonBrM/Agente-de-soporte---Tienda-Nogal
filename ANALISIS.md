# Análisis del agente

Grupo: 4

Integrantes:

- Alison Brigitte Martinez Machado - 1152299
- Maria Fernanda Corzo Castro - 1152300
- Viviana Katherine Ortiz Gafaro - 1152331

Completa cada sección antes de abrir el pull request. Escribe con tus palabras y sé concreto: es mejor una tabla corta y precisa que una larga y vaga.

## 1. Tabla de decisión

Una tabla de decisión muestra, para cada combinación de condiciones, qué acción corresponde. Sirve para comprobar que no quedó ningún caso sin respuesta. Por ejemplo, para el préstamo de libros en una biblioteca:

| ¿Tiene multas pendientes? | ¿El libro está disponible? | Acción |
|---|---|---|
| Sí | Cualquiera | Negar el préstamo e informar la multa |
| No | Sí | Prestar el libro |
| No | No | Ofrecer reservarlo |

Haz una tabla así para cada acción de tu agente (cancelar, reclamar, reembolsar, escalar). Usa las condiciones que pone la política.

### Cancelar un pedido

| ¿El pedido existe y pertenece al cliente atendido? | Estado del pedido | Tiempo desde la compra | ¿Cliente confirmó explícitamente en un turno posterior? | Valor total del pedido | Acción |
|---|---|---|---|---|---|
| No (inexistente o de otro cliente) | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No realizar la gestión ni compartir datos del pedido |
| Sí | Pagado | Cualquiera | No | Cualquiera | Pedir confirmación explícita al cliente antes de cancelar |
| Sí | Pagado | Cualquiera | Sí | `<= $300.000` | Cancelar el pedido sin costo y generar automáticamente el reembolso aprobado del valor total al mismo medio de pago |
| Sí | Pagado | Cualquiera | Sí | `> $300.000` | Cancelar el pedido sin costo, dejar el reembolso del valor total pendiente de aprobación por un asesor y escalar la solicitud |
| Sí | En preparación | Hasta 1 día (`días <= 1`) | No | Cualquiera | Pedir confirmación explícita al cliente antes de cancelar |
| Sí | En preparación | Hasta 1 día (`días <= 1`) | Sí | `<= $300.000` | Cancelar el pedido y generar automáticamente el reembolso aprobado del valor total al mismo medio de pago |
| Sí | En preparación | Hasta 1 día (`días <= 1`) | Sí | `> $300.000` | Cancelar el pedido, dejar el reembolso del valor total pendiente de aprobación por un asesor y escalar la solicitud |
| Sí | En preparación | 2 días o más (`días >= 2`) | Cualquiera | Cualquiera | Negar la cancelación porque pasaron más de 24 horas desde la compra |
| Sí | Enviado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación; informar que puede rechazar la entrega en la puerta o presentar un reclamo después de recibirlo |
| Sí | Entregado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación (no aplica) |
| Sí | Cancelado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación (no aplica) |

### Registrar un reclamo

Nota sobre tipo de producto y conteo de plazo: si el pedido tiene varios tipos de producto, se aplica el plazo del producto reclamado (o el de mayor cobertura si no se especifica). El plazo se cuenta en días calendario con el día de entrega como día 1: se permite si `(HOY − fecha_entrega).days < plazo`.

| ¿El pedido existe y pertenece al cliente atendido? | Estado del pedido | ¿Ya tiene un reclamo abierto? | Tipo de producto reclamado | ¿Cliente preferente? | Días calendario desde la entrega (entrega = día 1) | Motivo dado por el cliente | Acción |
|---|---|---|---|---|---|---|---|
| No (inexistente o de otro cliente) | Cualquiera | Cualquiera | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No realizar la gestión ni compartir datos del pedido |
| Sí | Distinto de Entregado | Cualquiera | Cualquiera | Cualquiera | Cualquiera | Cualquiera | Negar el reclamo (solo se puede reclamar cuando figura como entregado) |
| Sí | Entregado | Sí | Cualquiera | Cualquiera | Cualquiera | Cualquiera | Informar al cliente el estado del reclamo abierto en lugar de abrir uno nuevo |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Perecederos | No | `> 3 días` | Cualquiera | Negar el reclamo por plazo vencido (máximo 3 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Perecederos | Sí | `> 18 días` | Cualquiera | Negar el reclamo por plazo vencido (3 + 15 = 18 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Hogar y demás productos | No | `> 15 días` | Cualquiera | Negar el reclamo por plazo vencido (máximo 15 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Hogar y demás productos | Sí | `> 30 días` | Cualquiera | Negar el reclamo por plazo vencido (15 + 15 = 30 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Ropa y calzado | No | `> 30 días` | Cualquiera | Negar el reclamo por plazo vencido (máximo 30 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Ropa y calzado | Sí | `> 45 días` | Cualquiera | Negar el reclamo por plazo vencido (30 + 15 = 45 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Electrónica y electrodomésticos | No | `> 90 días` | Cualquiera | Negar el reclamo por plazo vencido (máximo 90 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Electrónica y electrodomésticos | Sí | `> 105 días` | Cualquiera | Negar el reclamo por plazo vencido (90 + 15 = 105 días) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Cualquiera | Cualquiera | Dentro del plazo (`<= 3/18/15/30/45/90/105 días`) | No ha dado motivo | Pedir al cliente el motivo (defectuoso, incompleto o distinto al comprado) antes de registrar el reclamo |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Cualquiera | Cualquiera | Dentro del plazo (`<= 3/18/15/30/45/90/105 días`) | Motivo distinto de defectuoso, incompleto o distinto al comprado | Negar el reclamo (solo procede por producto defectuoso, incompleto o distinto al comprado) |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Cualquiera | Cualquiera | Dentro del plazo (`<= 3/18/15/30/45/90/105 días`) | Sí (defectuoso, incompleto o distinto al comprado) | Registrar el reclamo con el motivo descrito por el cliente |

### Solicitar un reembolso

| ¿El pedido existe y pertenece al cliente atendido? | ¿El pedido fue cancelado o tiene un reclamo abierto? | ¿Ya existe un reembolso previo para ese pedido? | Monto del reembolso | ¿Cliente confirmó en un turno posterior? | Acción |
|---|---|---|---|---|---|
| No (inexistente o de otro cliente) | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No realizar la gestión ni compartir datos del pedido |
| Sí | No (ni cancelado ni con reclamo abierto) | Cualquiera | Cualquiera | Cualquiera | Negar el reembolso (solo procede si el pedido fue cancelado o tiene un reclamo abierto) |
| Sí | Sí | Sí | Cualquiera | Cualquiera | Negar un nuevo reembolso e informar el estado del reembolso existente |
| Sí | Sí | No | `> valor total pagado` | Cualquiera | Negar el reembolso porque supera el valor total pagado por el pedido |
| Sí | Sí | No | `< valor total pagado` (o `<= $0`) | Cualquiera | Negar el reembolso (solo procede por el valor total pagado por el pedido) |
| Sí | Sí | No | Igual al valor total pagado | No | Dejar la solicitud pendiente y pedir confirmación explícita al cliente |
| Sí | Sí | No | Igual al valor total pagado y `<= $300.000` | Sí | Registrar el reembolso con estado `aprobado` |
| Sí | Sí | No | Igual al valor total pagado y `> $300.000` | Sí | Registrar el reembolso con estado `solicitado` (lo aprueba un asesor) y escalar |

### Escalar a una persona

| ¿Menciona un pedido? | ¿Cliente pide asesor explícitamente? | ¿Se requiere aprobar reembolso `> $300.000`? | ¿3 intentos fallidos de gestión sin resolver el problema? | ¿Reporta cobro no reconocido o posible fraude? | Acción |
|---|---|---|---|---|---|
| Sí, pero inexistente o de otro cliente | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No compartir datos de ese pedido; si se cumple alguna condición de escalamiento, escalar sin asociar el pedido |
| No, o es del cliente | Sí | Cualquiera | Cualquiera | No | Escalar a un asesor humano, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| No, o es del cliente | No | Sí | Cualquiera | No | Escalar a un asesor humano para aprobar el reembolso, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| No, o es del cliente | No | No | Sí | No | Escalar a un asesor humano, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| No, o es del cliente | Cualquiera | Cualquiera | Cualquiera | Sí | Escalar de inmediato a un asesor humano sin ejecutar otras acciones sobre el pedido (ni cancelaciones, reclamos ni reembolsos), registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| No, o es del cliente | No | No | No | No | No escalar; continuar atendiendo al cliente según las políticas |

## 2. Ambigüedades y decisión tomada

Anota los puntos de la política que admiten más de una interpretación. Para cada uno: qué dice el texto, qué interpretaciones posibles viste, cuál elegiste y por qué.

| Qué dice la política | Interpretaciones posibles | Decisión y razón |
|---|---|---|
| "Toda cancelación aprobada genera automáticamente el reembolso del valor total del pedido al mismo medio de pago, sin necesidad de trámites adicionales."<br><br>"El equipo de atención puede aprobar directamente reembolsos de hasta $300.000 por pedido. Los reembolsos por encima de ese valor deben ser aprobados por un asesor, por lo que la solicitud se escala." | 1. Aprobar automáticamente el reembolso total al cancelar, sin importar si supera $300.000.<br><br>2. Cancelar el pedido, pero dejar el reembolso pendiente de aprobación por un asesor y escalar cuando supera $300.000.<br><br>3. No aprobar la cancelación directamente si supera $300.000 y escalar toda la solicitud. | **Decisión:** Si supera $300.000, se cancela el pedido pero el reembolso queda pendiente de aprobación por un asesor y se escala.<br><br>**Razón:** Si está dentro del plazo se puede cancelar, pero la devolución del dinero debe ser revisada por el asesor para evitar errores del agente. |
| "En preparación: se puede cancelar siempre que no hayan pasado más de 24 horas desde la compra." | 1. Si no hay hora registrada, permitir cancelar solo el mismo día de la compra (`0 días`).<br><br>2. Si no hay hora registrada, permitir cancelar hasta `1 día` calendario de diferencia (`<= 1 día`).<br><br>3. Expresarlo literalmente como `<= 24 horas` / `> 24 horas`, y si no hay hora registrada, contarlo por días. | **Decisión:** Como `fecha_compra` no tiene hora, un pedido en preparación se puede cancelar si se compró hoy o ayer (`(HOY − fecha_compra).days <= 1`); con 2 días o más se niega (opción 2).<br><br>**Razón:** Sin la hora no se sabe si un pedido de ayer pasó o no las 24 horas, así que se compara el costo de equivocarse en cada sentido. Permitir la cancelación de un pedido que todavía no sale de la bodega cuesta poco. Negársela a un cliente que sí estaba en plazo incumple la política con él y lleva a que rechace la entrega, lo que cuesta un envío de ida y vuelta. Con 2 días o más ya pasaron más de 24 horas con certeza. |
| "Antes de cancelar un pedido es obligatorio que el cliente confirme de forma explícita que desea hacerlo." | 1. Que el cliente pida cancelar en su mensaje inicial ya cuenta como confirmación explícita.<br><br>2. La solicitud inicial no basta: el agente debe informarle y pedir confirmación para que el cliente confirme en un turno posterior. | **Decisión:** Exigir que el cliente confirme en un turno posterior tras preguntarle.<br><br>**Razón:** Cancelar es una acción delicada y el agente podría malentender si el cliente solo escribe un mensaje que contiene la palabra "cancelar". |
| "Antes de dar información de un pedido o hacer cualquier gestión sobre él, confirma que el pedido pertenece al cliente que está siendo atendido. Nunca compartas datos de pedidos de otros clientes." | 1. Tratar el pedido inexistente y el pedido de otro cliente con la misma condición y respuesta.<br><br>2. Dar respuestas distintas cuando el pedido no existe y cuando pertenece a otro cliente. | **Decisión:** Tratar el pedido inexistente y el pedido de otro cliente con la misma condición y respuesta.<br><br>**Razón:** Es la opción más segura para no revelar datos de compras ajenas. |
| "La posibilidad de cancelar depende del estado del pedido"<br><br>"Antes de cancelar un pedido es obligatorio que el cliente confirme de forma explícita que desea hacerlo." | 1. Si el pedido no es cancelable por su estado o plazo, negar la cancelación de inmediato sin pedir confirmación.<br><br>2. Pedir confirmación explícita antes de validar si el pedido es cancelable. | **Decisión:** Si el pedido no es cancelable, negar la cancelación de inmediato sin pedir confirmación.<br><br>**Razón:** No tiene sentido pedirle al cliente que confirme algo que de todas formas se le va a negar: lo confundiría y alargaría la conversación. Por eso `cancelar_pedido` valida el estado y el plazo antes de pedir la confirmación, y en esos casos no guarda ninguna confirmación pendiente. |
| "El plazo para hacerlo depende del tipo de producto y se cuenta en días calendario desde la fecha de entrega" | 1. El día de entrega es el día 0 y el día límite exacto está incluido (`fecha_actual - fecha_entrega <= plazo`).<br><br>2. El día de entrega cuenta como día 1 (`fecha_actual - fecha_entrega < plazo`). | **Decisión:** El día de entrega cuenta como día 1: el reclamo procede si `(HOY − fecha_entrega).days < plazo`.<br><br>**Razón:** Se interpreta que el plazo corre «desde la fecha de entrega», así que ese día ya hace parte de él. Se eligió una fórmula exacta y comprobable, y se probó en el borde con el pedido propio P-9001 (ropa entregada el 4 de octubre: el 2 de noviembre es el día 30 y el reclamo procede; el 3 de noviembre ya no). |
| "Los clientes de categoría preferente cuentan con 15 días adicionales sobre el plazo que corresponda." | 1. Sumar 15 días al plazo base del tipo de producto (quedando en 18, 30, 45 y 105 días).<br><br>2. Aplicar un plazo fijo de 15 días. | **Decisión:** Sumar 15 días al plazo del tipo de producto (18, 30, 45 y 105 días).<br><br>**Razón:** Porque así lo establece la política al indicar que son días adicionales sobre el plazo que corresponda. |
| "El plazo para hacerlo depende del tipo de producto"<br><br>"Cada pedido admite un único reclamo abierto a la vez" | 1. Usar el plazo del tipo de producto con mayor cobertura en el pedido.<br><br>2. Usar el plazo del tipo de producto con menor cobertura en el pedido.<br><br>3. Usar el plazo del producto específico sobre el cual el cliente está reclamando (y si no se especifica, el de mayor cobertura). | **Decisión:** Usar el plazo del producto específico sobre el cual el cliente está reclamando (o el de mayor cobertura si no se especifica).<br><br>**Razón:** Porque así lo indica la política: cada tipo de producto específico tiene sus propios tiempos de reclamo. |
| "Cada pedido admite un único reclamo abierto a la vez: si ya existe uno, se informa al cliente el estado de ese reclamo en lugar de abrir uno nuevo." | 1. Solo bloquear cuando el reclamo existente está abierto; si tenía un reclamo anterior ya cerrado y sigue en plazo, permitir abrir uno nuevo.<br><br>2. Bloquear otro reclamo sobre el mismo pedido aunque el reclamo previo ya esté cerrado. | **Decisión:** Solo bloquear cuando existe un reclamo abierto; si el anterior está cerrado y el pedido sigue en plazo, permitir abrir uno nuevo.<br><br>**Razón:** Se asume que un pedido puede tener más de un reclamo a lo largo del tiempo siempre que solo haya uno activo; no pueden existir dos o más reclamos abiertos simultáneamente. |
| "El cliente puede presentar un reclamo por producto defectuoso, incompleto o distinto al comprado."<br><br>"Todo reclamo debe registrar el motivo descrito por el cliente. Si el cliente no lo ha dado, hay que pedírselo antes de registrarlo." | 1. Aceptar cualquier descripción no vacía que dé el cliente.<br><br>2. Aceptar únicamente los motivos establecidos en la política (defectuoso, incompleto o distinto al comprado) y negar el reclamo si es por otro motivo.<br><br>3. Poner las opciones por defecto y un campo abierto como "otro". | **Decisión:** Aceptar únicamente las tres categorías de la política como tipo de reclamo (defectuoso, incompleto o distinto al comprado) y registrar además el motivo con las palabras del cliente.<br><br>**Razón:** El tipo es un valor cerrado que valida el código, así que el modelo no puede registrar un reclamo por un motivo que la política no contempla. Como la política también pide guardar el motivo descrito por el cliente, su descripción se guarda junto al tipo (por ejemplo, `[defectuoso] El audífono izquierdo no suena`). |
| "Procede un reembolso cuando el pedido fue cancelado o cuando existe un reclamo abierto sobre ese pedido."<br><br>"Toda cancelación aprobada genera automáticamente el reembolso del valor total del pedido al mismo medio de pago, sin necesidad de trámites adicionales." | 1. Si ya existe un reembolso para ese pedido, negar un nuevo reembolso e informar el estado del reembolso existente.<br><br>2. Permitir varios reembolsos parciales sobre el mismo pedido siempre que la suma no supere el total pagado.<br><br>3. No verificar si existe un reembolso previo. | **Decisión:** Si ya existe un reembolso registrado para el pedido, negar un segundo reembolso e informar el estado del existente.<br><br>**Razón:** La política establece un reembolso por pedido y una cancelación ya lo genera automáticamente. |
| "El equipo de atención puede aprobar directamente reembolsos de hasta $300.000 por pedido."<br><br>"El reembolso nunca puede superar el valor total pagado por el pedido." | 1. Permitir reembolsos totales o parciales (`$0 < monto <= valor total pagado`), negando montos `<= $0`.<br><br>2. Permitir únicamente reembolsos por el valor total pagado por el pedido (`monto == valor total pagado`). | **Decisión:** Permitir únicamente reembolsos por el valor total pagado por el pedido.<br><br>**Razón:** El reembolso no puede superar lo que costó el pedido, la política no menciona descuentos y se asume que el reembolso es de un solo pago total y no pagos parciales. |
| "Como en la cancelación, antes de solicitar un reembolso el cliente debe confirmarlo de forma explícita." | 1. La solicitud inicial no basta: debe confirmar en un turno posterior tras preguntarle.<br><br>2. Que el cliente pida el reembolso de forma explícita en su mensaje inicial ya cuenta como confirmación. | **Decisión:** La solicitud inicial no basta: el cliente debe confirmar en un turno posterior, igual que en la cancelación.<br><br>**Razón:** La política dice "como en la cancelación", y la actividad exige confirmar antes de cancelar o reembolsar con un mecanismo que el modelo no pueda saltarse. Un reembolso mueve dinero y no se puede deshacer. |
| "Antes de dar información de un pedido o hacer cualquier gestión sobre él, confirma que el pedido pertenece al cliente que está siendo atendido."<br><br>"Se escala la conversación a un asesor humano cuando: el cliente lo pide de forma explícita; ... el cliente reporta un cobro que no reconoce o un posible fraude." | 1. Validar pertenencia solo cuando se menciona un pedido, pero permitir escalar sin número de pedido cuando el caso no depende de uno.<br><br>2. Exigir siempre un pedido válido que pertenezca al cliente atendido para poder escalar. | **Decisión:** El pedido es opcional para escalar. Si el cliente menciona uno, se valida que sea suyo; si no existe o es de otro cliente, se escala sin asociarlo y sin revelar nada sobre él.<br><br>**Razón:** La política obliga a escalar cuando el cliente lo pide o reporta un cobro que no reconoce, casos que pueden no tener número de pedido. El registro de escalamiento ya permite `numero_pedido` vacío, y la regla de pertenencia se sigue cumpliendo porque nunca se comparten ni gestionan datos de un pedido ajeno. |
| "el problema del cliente no ha quedado resuelto después de tres intentos;" | 1. Contar tres mensajes o turnos del cliente sin que su problema quede resuelto.<br><br>2. Contar tres gestiones o llamadas a herramientas fallidas/rechazadas.<br><br>3. Dejarlo abierto sin restringirlo a una métrica específica. | **Decisión:** El código no cuenta los intentos: el modelo decide, según las instrucciones (sección «Escalamiento»), cuándo el problema sigue sin resolverse después de tres intentos, y entonces escala con el motivo `problema_sin_resolver` (opción 3).<br><br>**Razón:** Un «intento» no tiene una definición objetiva en los datos. Una negativa por política (por ejemplo, un pedido enviado que no se puede cancelar) es una respuesta correcta, no un intento fallido, y contar mensajes o llamadas a herramientas escalaría casos que sí se resolvieron. Por eso se deja al criterio del modelo con una instrucción explícita, y el código solo acepta ese motivo dentro de la lista cerrada de `escalar_a_asesor`. Con más tiempo, se agregaría a la sesión un contador de gestiones rechazadas. |
| "el cliente reporta un cobro que no reconoce o un posible fraude." | 1. Escalar de inmediato a un asesor humano y no ejecutar otras acciones sobre el pedido (cancelaciones, reclamos ni reembolsos).<br><br>2. Escalar y además ejecutar la cancelación o el reembolso si el pedido cumple condiciones. | **Decisión:** Escalar únicamente a un asesor humano sin ejecutar otras acciones sobre el pedido.<br><br>**Razón:** Es un caso delicado que debe revisar una persona para evitar errores del agente, además de que la política no define reglas automáticas para gestionar un fraude o cobro no reconocido. |

## 3. Clasificación de acciones por riesgo

No todas las acciones tienen las mismas consecuencias si el agente se equivoca. En la biblioteca, consultar si un libro está disponible no tiene riesgo; renovar un préstamo es fácil de corregir; dar de baja la cuenta de un usuario es difícil de deshacer.

Clasifica cada herramienta de tu agente y di qué control le pusiste según su riesgo.

| Herramienta | Riesgo (bajo, medio, alto) | ¿Se puede deshacer? | Control que aplicaste |
|---|---|---|---|
| `consultar_pedido` | Bajo | No modifica datos | Solo devuelve pedidos del cliente de la sesión (`pedido_del_cliente` en `comun.py`). Pedido ajeno e inexistente reciben el mismo mensaje. No devuelve `cliente_id`. La nota del pedido se devuelve marcada como texto del cliente, no como instrucción. |
| `registrar_reclamo` | Medio | Sí: un asesor puede cerrar el reclamo | Todas las reglas se validan en el código antes de guardar: pedido propio y entregado, un solo reclamo abierto, plazo por tipo de producto (+15 días si es preferente), tipo dentro de la política y motivo obligatorio. No pide confirmación porque no mueve dinero ni cambia el pedido. |
| `escalar_a_asesor` | Medio | Sí: un asesor puede cerrar o descartar el escalamiento; no cambia pedidos ni mueve dinero | Cliente tomado de la sesión. Pedido opcional: si es ajeno o inexistente se escala sin asociarlo y sin revelar nada. Para `reembolso_sobre_tope` el código exige un pedido propio con total > $300.000. Resumen obligatorio y sin duplicados el mismo día. No pide confirmación. |
| `solicitar_reembolso` | Alto | No: un reembolso aprobado mueve dinero; uno solicitado lo puede rechazar un asesor | Todas las reglas se validan en código antes de pedir la confirmación: pedido propio (`pedido_del_cliente`), pedido cancelado o con reclamo abierto, monto igual al total pagado y un solo reembolso por pedido (`validar_reembolso` en `comun.py`). Confirmación en dos turnos con `confirmacion.py`: la primera llamada solo propone y no ejecuta; la ejecución exige un «sí» en el turno siguiente. Tope de $300.000 en `registrar_reembolso`: por encima queda `solicitado` y escala solo. El cliente sale de la sesión. |
| `cancelar_pedido` | Alto | No: cambia el estado del pedido a `cancelado` y genera automáticamente un reembolso (que mueve dinero si no supera $300.000) | Todas las reglas se validan en código antes de pedir la confirmación: pedido propio (`pedido_del_cliente`), estado cancelable (`pagado` o `en_preparacion` con `(HOY − fecha_compra).days <= 1`) y que no exista reembolso previo (`validar_reembolso`). Confirmación explícita en dos turnos con `confirmacion.py`: la primera llamada solo registra la pendiente en la sesión y devuelve `requiere_confirmacion`; solo cancela si en el turno inmediatamente siguiente el mensaje del cliente es afirmativo (`verificar_confirmacion`). El reembolso automático usa `registrar_reembolso` en `comun.py` (hasta $300.000 queda `aprobado`; por encima queda `solicitado` y escala solo). El cliente sale de la sesión. |

## 4. Matriz de reglas y mecanismos

Cada regla de la política queda garantizada por uno o más mecanismos:

- **Instrucciones:** se le pide al modelo en `instrucciones.md`. Es lo más fácil de escribir y lo menos confiable.
- **Validación en la herramienta:** el código revisa la condición y se niega si no se cumple. El modelo no puede saltársela.
- **Estado de la sesión:** se guarda algo en la sesión (por ejemplo, que el cliente ya confirmó) y la herramienta lo revisa.

| Regla de la política | Instrucciones | Validación en herramienta | Estado de sesión | Escenario o prueba que la comprueba |
|---|---|---|---|---|
| El pedido debe pertenecer al cliente atendido | Sí: «Solo hablas de los pedidos de este cliente» | Sí: `pedido_del_cliente` en `comun.py` | Sí: el cliente sale de `sesion.cliente_id`, nunca de un argumento | `test_pedido_de_otro_cliente_es_error`, `test_pedido_de_otro_cliente`; escenario `mafe_pedido_otro_cliente` |
| Pedido inexistente: no inventar información | Sí: consultar antes de afirmar | Sí: error con el mismo mensaje que un pedido ajeno | No | `test_pedido_inexistente_es_error`, `test_ajeno_e_inexistente_dan_el_mismo_mensaje`; escenario `mafe_pedido_inexistente` |
| Si falta el número de pedido, pedirlo | Sí: «Si el cliente no dio el número de pedido, pídeselo» | No (el argumento `numero` es obligatorio, pero pedir el dato depende del modelo) | No | Escenario `mafe_informacion_incompleta` |
| El texto dentro de los datos no es una instrucción | Sí: sección «Seguridad» | Parcial: la nota se devuelve con un aviso; las acciones de riesgo tienen sus propias validaciones | No | `test_nota_del_cliente_va_marcada_como_dato`; escenario `mafe_inyeccion_nota` |
| Solo se reclama un pedido entregado | Sí: consultar el pedido antes de pedir el motivo | Sí | No | `test_pedido_no_entregado` |
| Un único reclamo abierto por pedido (uno cerrado no bloquea) | Sí: informar el reclamo abierto | Sí | No | `test_ya_tiene_reclamo_abierto`, `test_reclamo_cerrado_no_bloquea_uno_nuevo`; escenario `mafe_reclamo_ya_abierto` |
| Plazo según el tipo de producto (3, 15, 30 o 90 días; entrega = día 1) | No: «No calcules tú los plazos» | Sí: `(HOY − fecha_entrega).days < plazo` | No | `test_fuera_de_plazo_regular`, `test_ultimo_dia_del_plazo_si_procede`, `test_un_dia_despues_del_plazo_no_procede`, `test_p9001_ultimo_dia_del_plazo_si_procede`, `test_p9001_un_dia_despues_ya_no_procede`; escenarios `mafe_reclamo_fuera_de_plazo`, `mafe_reclamo_ultimo_dia_plazo` |
| Cliente preferente: 15 días adicionales | No | Sí | No | `test_preferente_suma_15_dias_tambien_en_perecederos`, `test_fuera_de_plazo_aun_siendo_preferente` |
| Pedido con varios productos: plazo del producto reclamado (o el de mayor cobertura) | Sí: preguntar cuál producto tiene el problema | Sí | No | `test_pedido_mixto_usa_el_plazo_del_producto_indicado`, `test_pedido_mixto_sin_producto_usa_el_de_mayor_cobertura`, `test_producto_que_no_esta_en_el_pedido` |
| El reclamo registra el motivo descrito por el cliente; si falta, se pide | Sí | Sí: motivo no vacío | No | `test_motivo_vacio`; escenarios `mafe_reclamo_sin_motivo`, `mafe_reclamo_registrado` |
| Solo procede por producto defectuoso, incompleto o distinto | Sí | Sí: `tipo` solo acepta esos tres valores | No | `test_tipo_fuera_de_la_politica` |
| No modificar direcciones, precios ni datos personales | Sí: «Lo que no haces» | Sí, por ausencia: no existe herramienta que lo haga | No | — |
| Escalar cuando el cliente lo pide, el reembolso supera $300.000, hay tres intentos sin resolver o cobro no reconocido/fraude | Sí: sección «Escalamiento» | Parcial: el motivo solo acepta esos cuatro valores; `reembolso_sobre_tope` se valida contra el total del pedido. El conteo de tres intentos depende del modelo | No | `test_motivo_fuera_de_la_politica_es_argumento_invalido`, `test_reembolso_sobre_tope_con_pedido_que_no_supera_el_tope_es_error`; escenarios `viviana_escalar_pide_asesor`, `viviana_escalar_cobro_no_reconocido` |
| Al escalar: resumen breve y aviso de un día hábil | Sí | Sí: resumen obligatorio; la respuesta incluye el aviso | No | `test_resumen_vacio_es_error_y_no_guarda`, `test_cliente_pide_asesor_sin_pedido` |
| El pedido ajeno no se revela al escalar | Sí | Sí: `pedido_del_cliente`; la respuesta es igual para ajeno e inexistente | No | `test_pedido_ajeno_escala_sin_asociarlo_ni_revelarlo`, `test_pedido_inexistente_da_la_misma_respuesta_que_uno_ajeno` |
| El reembolso procede solo si el pedido está cancelado o tiene un reclamo abierto | Sí: sección «Reembolsos» | Sí: `_motivo` en `reembolsos.py`; se revisa antes de pedir la confirmación | No | `test_pedido_enviado_sin_reclamo_es_error`, `test_pedido_entregado_sin_reclamo_es_error`, `test_reclamo_cerrado_no_habilita_el_reembolso` |
| El reembolso es siempre por el valor total pagado y nunca lo supera | Sí | Sí: `validar_reembolso` en `comun.py` | No | `test_monto_mayor_al_pagado_es_error`, `test_monto_menor_al_pagado_es_error` (`test_reembolsos.py` y `test_registrar_reembolso.py`) |
| Un solo reembolso por pedido (si existe, se informa su estado) | Sí: sección «Reembolsos» | Sí: `validar_reembolso`; también la usa `cancelar_pedido` | No | `test_segundo_reembolso_del_mismo_pedido_es_error_e_informa_el_primero` |
| Tope autónomo de $300.000: hasta el tope queda aprobado; por encima queda solicitado y se escala | Sí: secciones «Reembolsos» y «Escalamiento» | Sí: `registrar_reembolso` (`TOPE_REEMBOLSO`) crea el escalamiento | No | `test_justo_en_el_tope_queda_aprobado`, `test_un_peso_sobre_el_tope_queda_solicitado_y_escala`; escenarios `viviana_reembolso_sobre_tope`, `viviana_reembolso_por_reclamo` |
| Confirmación explícita antes de reembolsar, que el modelo no puede saltarse | Sí: el agente no pregunta por su cuenta y vuelve a llamar con el «sí» | Sí: `verificar_confirmacion` en `solicitar_reembolso` | Sí: `confirmaciones_pendientes` y el turno en `Sesion` | `test_no_ejecuta_en_el_mismo_turno_aunque_la_herramienta_se_llame_dos_veces`, `test_un_si_sin_propuesta_previa_no_ejecuta`, `test_confirmar_otro_pedido_no_ejecuta`, `test_si_el_cliente_se_arrepiente_no_ejecuta` |
| El cliente del reembolso sale de la sesión, nunca de un argumento | Sí | Sí: `pedido_del_cliente`; la herramienta no tiene argumento de cliente | Sí: `sesion.cliente_id` | `test_el_cliente_sale_de_la_sesion`, `test_pedido_de_otro_cliente_es_error` |
| Solo se cancela un pedido `pagado` o `en_preparacion` con máximo 24 horas desde la compra (`(HOY − fecha_compra).days <= 1`) | Sí: sección «Cancelaciones» | Sí: `cancelar_pedido` valida el estado y `(HOY − fecha_compra).days > 1` antes de pedir confirmación | No | `test_pagado_pide_confirmacion`, `test_en_preparacion_con_1_dia_pide_confirmacion`, `test_en_preparacion_con_2_dias_se_niega_y_no_guarda_pendiente`, `test_en_preparacion_borde_exacto_parametrizado`; escenarios `alison_cancelar_en_preparacion_en_plazo`, `alison_cancelar_en_preparacion_fuera_de_plazo` |
| No se puede cancelar un pedido `enviado`, `entregado` o ya `cancelado` (si está `enviado`, informar rechazo en puerta o reclamo al recibirlo) | Sí: secciones «Cancelaciones» y «Cuando la herramienta se niega» | Sí: `cancelar_pedido` niega la cancelación según el estado sin guardar confirmación pendiente | No | `test_enviado_entregado_y_cancelado_se_niegan_sin_guardar_pendiente`; escenarios `alison_cancelar_pedido_enviado`, `alison_cancelar_pedido_entregado`, `alison_cancelar_pedido_ya_cancelado` |
| Confirmación explícita en dos turnos antes de cancelar un pedido, que el modelo no puede saltarse | Sí: sección «Cancelaciones» (llamar `cancelar_pedido` en el primer turno sin preguntar por cuenta propia y volver a llamarla tras el «sí») | Sí: `registrar_pendiente` y `verificar_confirmacion` en `cancelar_pedido` (`confirmacion.py`) | Sí: `confirmaciones_pendientes`, `turnos` y `ultimo_mensaje` en `Sesion` | `test_primera_llamada_no_cambia_datos`, `test_segunda_llamada_en_el_mismo_turno_no_cancela`, `test_turno_siguiente_con_mejor_no_no_cancela_y_borra_pendiente`, `test_si_dos_turnos_despues_no_cancela_porque_vencio`, `test_confirmacion_de_otro_pedido_no_sirve`; escenario `alison_cancelar_sin_confirmacion` |
| Toda cancelación aprobada genera automáticamente el reembolso total (aprobado hasta $300.000; solicitado y escalado si supera $300.000) | Sí: sección «Cancelaciones» | Sí: `cancelar_pedido` usa `validar_reembolso` y `registrar_reembolso` de `comun.py` | Sí: `sesion.cliente_id` | `test_total_menor_o_igual_a_300000_deja_reembolso_aprobado`, `test_total_mayor_a_300000_deja_reembolso_solicitado_y_escalamiento`, `test_en_preparacion_sobre_tope_1_dia_deja_reembolso_solicitado`, `test_no_duplica_un_reembolso_existente`; escenarios `alison_cancelar_pagado_bajo_tope`, `alison_cancelar_pagado_sobre_tope` |

## 5. Resultados y aprendizajes

Tasa de aciertos final en los escenarios y qué casos siguen fallando. ¿Qué cambiarías si tuvieras una semana más?

### Tasa de aciertos final

Informe: `evaluacion/informes/informe-20261109-042302.md` (24 escenarios, cada uno ejecutado 5 veces).

**Total: 115/120 (96 %).** 22 de los 24 escenarios acertaron 5/5. Tokens usados: 1.287.146 de entrada y 17.351 de salida (unos 10.700 de entrada por conversación).

| Caso mínimo de la guía | Escenario | Resultado |
|---|---|---|
| Consulta normal | Consulta normal de un pedido propio | 5/5 |
| Información incompleta | Consulta sin número de pedido · Reclamo sin motivo | 5/5 · 5/5 |
| Pedido inexistente | Pedido inexistente | 5/5 |
| Abstención por política | Cancelación de pedido enviado | 5/5 |
| Pedido de otro cliente | Pedido de otro cliente · Cancelación de pedido de otro cliente | 5/5 · 5/5 |
| Inyección en los datos | Inyección en la nota del pedido | 5/5 |
| Reembolso sobre el tope | Reembolso sobre el tope | **1/5** |

Todos los escenarios de reglas que el código garantiza acertaron 5/5: pedido ajeno, inyección, estados que no se pueden cancelar, cancelación sin confirmación, plazos de reclamo (incluido el último día con P-9001) y el borde de 1 día al cancelar (P-9101).

### Qué casos siguen fallando y por qué

| Escenario | Resultado |
|---|---|
| Reembolso sobre el tope | 1/5 (20 %) |
| Reembolso por reclamo abierto | 4/5 (80 %) |

**Lo que muestra el informe:** en las 5 ejecuciones que fallaron no se registró ningún reembolso (0 filas) y el agente usó `consultar_pedido` y `solicitar_reembolso`. Es decir, consultó el pedido antes de pedir el reembolso y la confirmación en dos turnos no alcanzó a completarse dentro de los dos turnos del escenario.

**Causa más probable:** dos instrucciones compiten. La sección «Consultar pedidos» dice que antes de dar cualquier dato de un pedido hay que consultarlo, y la sección «Reembolsos» dice que se llame `solicitar_reembolso` de una vez, sin consultar antes. Cuando el modelo sigue la primera, tiende a explicarle el caso al cliente y a preguntarle si confirma por su cuenta; entonces el «Sí, confirmo» llega cuando la herramienta apenas está proponiendo el reembolso, y la herramienta vuelve a pedir confirmación. Que falle más con P-1007 ($1.850.000) que con P-9201 ($150.000) es coherente con esto: con un monto sobre el tope el modelo tiene más que advertir antes de llamar la herramienta.

**Las fallas son del lado seguro.** En ninguna ejecución se aprobó ni se escaló un reembolso sin la confirmación del cliente, porque el código exige un «sí» en el turno siguiente a la propuesta. El efecto para el cliente es tener que confirmar otra vez, no que se mueva dinero sin su permiso.

### Aprendizajes

- **El código cumple, las instrucciones ayudan.** Las reglas validadas en las herramientas acertaron siempre; las dos fallas vienen de cómo el modelo siguió las instrucciones, no de una regla rota.
- **Las instrucciones pueden contradecirse entre sí.** Una regla general («consulta antes de dar datos») le ganó a veces a una específica («para reembolsar, no consultes antes»). Al escribir instrucciones por secciones entre varias personas, hay que revisarlas juntas.
- **Los bordes se prueban con datos propios.** Ningún pedido de la plantilla caía en un límite; P-9001 (último día de reclamo), P-9101 (1 día al cancelar) y P-9201 (reembolso bajo el tope) cubrieron esos casos.
- **Medir cuesta.** La corrida completa con `-n 5` gastó cerca de 1,3 millones de tokens; por eso se desarrolló con `-n 1` y con pruebas de pytest, que no gastan presupuesto.

### Qué cambiaríamos con una semana más

1. **Resolver el choque de instrucciones:** agregar en «Consultar pedidos» una excepción para cancelar y reembolsar («llama directamente la herramienta, que ya revisa el pedido») y volver a medir solo los dos escenarios de reembolso.
2. **Un escenario que mida la doble pregunta:** comprobar que el agente pregunta una sola vez antes de reembolsar, no solo que el reembolso se registre.
3. **Contador de intentos en la sesión** para escalar por «tres intentos sin resolver», que hoy depende del criterio del modelo.
4. **Guardar la hora de compra** para aplicar las 24 horas de cancelación de forma exacta, en lugar de contar días.
