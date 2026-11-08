# Análisis del agente

Grupo:
Integrantes:

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
| Sí | En preparación | Mismo día (`días == 0`) | No | Cualquiera | Pedir confirmación explícita al cliente antes de cancelar |
| Sí | En preparación | Mismo día (`días == 0`) | Sí | `<= $300.000` | Cancelar el pedido y generar automáticamente el reembolso aprobado del valor total al mismo medio de pago |
| Sí | En preparación | Mismo día (`días == 0`) | Sí | `> $300.000` | Cancelar el pedido, dejar el reembolso del valor total pendiente de aprobación por un asesor y escalar la solicitud |
| Sí | En preparación | 1 día o más (`días >= 1`) | Cualquiera | Cualquiera | Negar la cancelación porque pasaron más de 24 horas desde la compra |
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
| "En preparación: se puede cancelar siempre que no hayan pasado más de 24 horas desde la compra." | 1. Si no hay hora registrada, permitir cancelar solo el mismo día de la compra (`0 días`).<br><br>2. Si no hay hora registrada, permitir cancelar hasta `1 día` calendario de diferencia (`<= 1 día`).<br><br>3. Expresarlo literalmente como `<= 24 horas` / `> 24 horas`, y si no hay hora registrada, contarlo por días. | **Decisión:** Como `fecha_compra` no tiene hora, un pedido en preparación se puede cancelar solo si se compró el mismo día (`(HOY − fecha_compra).days == 0`); con 1 día o más se niega.<br><br>**Razón:** Sin la hora no se puede probar que no han pasado 24 horas: un pedido de ayer pudo comprarse hace más de 24 horas. Ante la duda se aplica la lectura que no incumple la política. |
| "Antes de cancelar un pedido es obligatorio que el cliente confirme de forma explícita que desea hacerlo." | 1. Que el cliente pida cancelar en su mensaje inicial ya cuenta como confirmación explícita.<br><br>2. La solicitud inicial no basta: el agente debe informarle y pedir confirmación para que el cliente confirme en un turno posterior. | **Decisión:** Exigir que el cliente confirme en un turno posterior tras preguntarle.<br><br>**Razón:** Cancelar es una acción delicada y el agente podría malentender si el cliente solo escribe un mensaje que contiene la palabra "cancelar". |
| "Antes de dar información de un pedido o hacer cualquier gestión sobre él, confirma que el pedido pertenece al cliente que está siendo atendido. Nunca compartas datos de pedidos de otros clientes." | 1. Tratar el pedido inexistente y el pedido de otro cliente con la misma condición y respuesta.<br><br>2. Dar respuestas distintas cuando el pedido no existe y cuando pertenece a otro cliente. | **Decisión:** Tratar el pedido inexistente y el pedido de otro cliente con la misma condición y respuesta.<br><br>**Razón:** Es la opción más segura para no revelar datos de compras ajenas. |
| "La posibilidad de cancelar depende del estado del pedido"<br><br>"Antes de cancelar un pedido es obligatorio que el cliente confirme de forma explícita que desea hacerlo." | 1. Si el pedido no es cancelable por su estado o plazo, negar la cancelación de inmediato sin pedir confirmación.<br><br>2. Pedir confirmación explícita antes de validar si el pedido es cancelable. | **Decisión:** Si el pedido no es cancelable, negar la cancelación de inmediato sin pedir confirmación.<br><br>**Razón:** Por regla del negocio, si el pedido no es cancelable tampoco procede gestionar su cancelación ni el reembolso. |
| "El plazo para hacerlo depende del tipo de producto y se cuenta en días calendario desde la fecha de entrega" | 1. El día de entrega es el día 0 y el día límite exacto está incluido (`fecha_actual - fecha_entrega <= plazo`).<br><br>2. El día de entrega cuenta como día 1 (`fecha_actual - fecha_entrega < plazo`). | **Decisión:** El día de entrega cuenta como día 1.<br><br>**Razón:** El plazo empieza a contar desde el mismo día de la entrega. |
| "Los clientes de categoría preferente cuentan con 15 días adicionales sobre el plazo que corresponda." | 1. Sumar 15 días al plazo base del tipo de producto (quedando en 18, 30, 45 y 105 días).<br><br>2. Aplicar un plazo fijo de 15 días. | **Decisión:** Sumar 15 días al plazo del tipo de producto (18, 30, 45 y 105 días).<br><br>**Razón:** Porque así lo establece la política al indicar que son días adicionales sobre el plazo que corresponda. |
| "El plazo para hacerlo depende del tipo de producto"<br><br>"Cada pedido admite un único reclamo abierto a la vez" | 1. Usar el plazo del tipo de producto con mayor cobertura en el pedido.<br><br>2. Usar el plazo del tipo de producto con menor cobertura en el pedido.<br><br>3. Usar el plazo del producto específico sobre el cual el cliente está reclamando (y si no se especifica, el de mayor cobertura). | **Decisión:** Usar el plazo del producto específico sobre el cual el cliente está reclamando (o el de mayor cobertura si no se especifica).<br><br>**Razón:** Porque así lo indica la política: cada tipo de producto específico tiene sus propios tiempos de reclamo. |
| "Cada pedido admite un único reclamo abierto a la vez: si ya existe uno, se informa al cliente el estado de ese reclamo en lugar de abrir uno nuevo." | 1. Solo bloquear cuando el reclamo existente está abierto; si tenía un reclamo anterior ya cerrado y sigue en plazo, permitir abrir uno nuevo.<br><br>2. Bloquear otro reclamo sobre el mismo pedido aunque el reclamo previo ya esté cerrado. | **Decisión:** Solo bloquear cuando existe un reclamo abierto; si el anterior está cerrado y el pedido sigue en plazo, permitir abrir uno nuevo.<br><br>**Razón:** Se asume que un pedido puede tener más de un reclamo a lo largo del tiempo siempre que solo haya uno activo; no pueden existir dos o más reclamos abiertos simultáneamente. |
| "El cliente puede presentar un reclamo por producto defectuoso, incompleto o distinto al comprado."<br><br>"Todo reclamo debe registrar el motivo descrito por el cliente. Si el cliente no lo ha dado, hay que pedírselo antes de registrarlo." | 1. Aceptar cualquier descripción no vacía que dé el cliente.<br><br>2. Aceptar únicamente los motivos establecidos en la política (defectuoso, incompleto o distinto al comprado) y negar el reclamo si es por otro motivo.<br><br>3. Poner las opciones por defecto y un campo abierto como "otro". | **Decisión:** Aceptar únicamente las categorías establecidas en la política (producto defectuoso, incompleto o distinto al comprado).<br><br>**Razón:** Habilitar un campo abierto para otros motivos podría confundir al agente, por lo que se restringe a las categorías definidas en la política. |
| "Procede un reembolso cuando el pedido fue cancelado o cuando existe un reclamo abierto sobre ese pedido."<br><br>"Toda cancelación aprobada genera automáticamente el reembolso del valor total del pedido al mismo medio de pago, sin necesidad de trámites adicionales." | 1. Si ya existe un reembolso para ese pedido, negar un nuevo reembolso e informar el estado del reembolso existente.<br><br>2. Permitir varios reembolsos parciales sobre el mismo pedido siempre que la suma no supere el total pagado.<br><br>3. No verificar si existe un reembolso previo. | **Decisión:** Si ya existe un reembolso registrado para el pedido, negar un segundo reembolso e informar el estado del existente.<br><br>**Razón:** La política establece un reembolso por pedido y una cancelación ya lo genera automáticamente. |
| "El equipo de atención puede aprobar directamente reembolsos de hasta $300.000 por pedido."<br><br>"El reembolso nunca puede superar el valor total pagado por el pedido." | 1. Permitir reembolsos totales o parciales (`$0 < monto <= valor total pagado`), negando montos `<= $0`.<br><br>2. Permitir únicamente reembolsos por el valor total pagado por el pedido (`monto == valor total pagado`). | **Decisión:** Permitir únicamente reembolsos por el valor total pagado por el pedido.<br><br>**Razón:** El reembolso no puede superar lo que costó el pedido, la política no menciona descuentos y se asume que el reembolso es de un solo pago total y no pagos parciales. |
| "Como en la cancelación, antes de solicitar un reembolso el cliente debe confirmarlo de forma explícita." | 1. La solicitud inicial no basta: debe confirmar en un turno posterior tras preguntarle.<br><br>2. Que el cliente pida el reembolso de forma explícita en su mensaje inicial ya cuenta como confirmación. | **Decisión:** La solicitud inicial no basta: el cliente debe confirmar en un turno posterior, igual que en la cancelación.<br><br>**Razón:** La política dice "como en la cancelación", y la actividad exige confirmar antes de cancelar o reembolsar con un mecanismo que el modelo no pueda saltarse. Un reembolso mueve dinero y no se puede deshacer. |
| "Antes de dar información de un pedido o hacer cualquier gestión sobre él, confirma que el pedido pertenece al cliente que está siendo atendido."<br><br>"Se escala la conversación a un asesor humano cuando: el cliente lo pide de forma explícita; ... el cliente reporta un cobro que no reconoce o un posible fraude." | 1. Validar pertenencia solo cuando se menciona un pedido, pero permitir escalar sin número de pedido cuando el caso no depende de uno.<br><br>2. Exigir siempre un pedido válido que pertenezca al cliente atendido para poder escalar. | **Decisión:** El pedido es opcional para escalar. Si el cliente menciona uno, se valida que sea suyo; si no existe o es de otro cliente, se escala sin asociarlo y sin revelar nada sobre él.<br><br>**Razón:** La política obliga a escalar cuando el cliente lo pide o reporta un cobro que no reconoce, casos que pueden no tener número de pedido. El registro de escalamiento ya permite `numero_pedido` vacío, y la regla de pertenencia se sigue cumpliendo porque nunca se comparten ni gestionan datos de un pedido ajeno. |
| "el problema del cliente no ha quedado resuelto después de tres intentos;" | 1. Contar tres mensajes o turnos del cliente sin que su problema quede resuelto.<br><br>2. Contar tres gestiones o llamadas a herramientas fallidas/rechazadas.<br><br>3. Dejarlo abierto sin restringirlo a una métrica específica. | **Decisión:** Contar tres intentos fallidos de gestión sin resolver el problema.<br><br>**Razón:** Así lo establece la política y evita que el agente se quede bloqueado intentando resolver el mismo problema indefinidamente. |
| "el cliente reporta un cobro que no reconoce o un posible fraude." | 1. Escalar de inmediato a un asesor humano y no ejecutar otras acciones sobre el pedido (cancelaciones, reclamos ni reembolsos).<br><br>2. Escalar y además ejecutar la cancelación o el reembolso si el pedido cumple condiciones. | **Decisión:** Escalar únicamente a un asesor humano sin ejecutar otras acciones sobre el pedido.<br><br>**Razón:** Es un caso delicado que debe revisar una persona para evitar errores del agente, además de que la política no define reglas automáticas para gestionar un fraude o cobro no reconocido. |
| "Al escalar se registra un resumen breve del caso para que el asesor no tenga que volver a preguntar lo mismo, y se le informa al cliente que un asesor lo contactará en un plazo máximo de un día hábil." | 1. Incluir el registro del resumen breve y el aviso de contacto en un día hábil como parte de la acción en la tabla de escalamiento.<br><br>2. Ponerlo como una columna de condición adicional o repetir ese detalle también en la tabla de reembolsos. | **Decisión:** Dejar el registro del resumen breve y el aviso de 1 día hábil como parte de la columna de acción en la tabla de escalar.<br><br>**Razón:** Por facilidad y simplicidad en la estructura de las tablas. |

## 3. Clasificación de acciones por riesgo

No todas las acciones tienen las mismas consecuencias si el agente se equivoca. En la biblioteca, consultar si un libro está disponible no tiene riesgo; renovar un préstamo es fácil de corregir; dar de baja la cuenta de un usuario es difícil de deshacer.

Clasifica cada herramienta de tu agente y di qué control le pusiste según su riesgo.

| Herramienta | Riesgo (bajo, medio, alto) | ¿Se puede deshacer? | Control que aplicaste |
|---|---|---|---|
| `consultar_pedido` | Bajo | No modifica datos | Solo devuelve pedidos del cliente de la sesión (`pedido_del_cliente` en `comun.py`). Pedido ajeno e inexistente reciben el mismo mensaje. No devuelve `cliente_id`. La nota del pedido se devuelve marcada como texto del cliente, no como instrucción. |
| `registrar_reclamo` | Medio | Sí: un asesor puede cerrar el reclamo | Todas las reglas se validan en el código antes de guardar: pedido propio y entregado, un solo reclamo abierto, plazo por tipo de producto (+15 días si es preferente), tipo dentro de la política y motivo obligatorio. No pide confirmación porque no mueve dinero ni cambia el pedido. |

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

## 5. Resultados y aprendizajes

Tasa de aciertos final en los escenarios y qué casos siguen fallando. ¿Qué cambiarías si tuvieras una semana más?