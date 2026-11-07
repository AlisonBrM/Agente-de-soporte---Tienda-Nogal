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
| Sí | En preparación | `<= 24 horas` | No | Cualquiera | Pedir confirmación explícita al cliente antes de cancelar |
| Sí | En preparación | `<= 24 horas` | Sí | `<= $300.000` | Cancelar el pedido y generar automáticamente el reembolso aprobado del valor total al mismo medio de pago |
| Sí | En preparación | `<= 24 horas` | Sí | `> $300.000` | Cancelar el pedido, dejar el reembolso del valor total pendiente de aprobación por un asesor y escalar la solicitud |
| Sí | En preparación | `> 24 horas` | Cualquiera | Cualquiera | Negar la cancelación porque pasaron más de 24 horas desde la compra |
| Sí | Enviado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación; informar que puede rechazar la entrega en la puerta o presentar un reclamo después de recibirlo |
| Sí | Entregado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación (no aplica) |
| Sí | Cancelado | Cualquiera | Cualquiera | Cualquiera | Negar la cancelación (no aplica) |

### Registrar un reclamo

Nota sobre tipo de producto y conteo de plazo: si el pedido tiene varios tipos de producto, se aplica el plazo del producto reclamado (o el de mayor cobertura si no se especifica). El plazo se cuenta en días calendario con el día de entrega como día 1.

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
| Sí | Entregado | No (sin reclamo o solo cerrado) | Cualquiera | Cualquiera | Dentro del plazo (`<= 3/18/15/30/45/90/105 días`) | No ha dado motivo | Pedir al cliente el motivo (opciones por defecto: defectuoso, incompleto, distinto al comprado, u "otro" con descripción en texto) antes de registrar el reclamo |
| Sí | Entregado | No (sin reclamo o solo cerrado) | Cualquiera | Cualquiera | Dentro del plazo (`<= 3/18/15/30/45/90/105 días`) | Sí (opción por defecto: defectuoso, incompleto, distinto al comprado, u "otro" con texto) | Registrar el reclamo con el motivo descrito por el cliente |

### Solicitar un reembolso

| ¿El pedido existe y pertenece al cliente atendido? | ¿El pedido fue cancelado o tiene un reclamo abierto? | ¿Ya existe un reembolso previo para ese pedido? | Monto del reembolso | ¿Cliente solicitó/confirmó explícitamente? | Acción |
|---|---|---|---|---|---|
| No (inexistente o de otro cliente) | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No realizar la gestión ni compartir datos del pedido |
| Sí | No (ni cancelado ni con reclamo abierto) | Cualquiera | Cualquiera | Cualquiera | Negar el reembolso (solo procede si el pedido fue cancelado o tiene un reclamo abierto) |
| Sí | Sí | Sí | Cualquiera | Cualquiera | Negar un nuevo reembolso e informar el estado del reembolso existente |
| Sí | Sí | No | `> valor total pagado` | Cualquiera | Negar el reembolso porque supera el valor total pagado por el pedido |
| Sí | Sí | No | `< valor total pagado` (o `<= $0`) | Cualquiera | Negar el reembolso (solo procede por el valor total pagado por el pedido) |
| Sí | Sí | No | Igual al valor total pagado | No | Pedir confirmación explícita al cliente antes de solicitar el reembolso |
| Sí | Sí | No | Igual al valor total pagado y `<= $300.000` | Sí (basta la solicitud explícita del cliente) | Aprobar directamente el reembolso |
| Sí | Sí | No | Igual al valor total pagado y `> $300.000` | Sí (basta la solicitud explícita del cliente) | Dejar el reembolso pendiente de aprobación por un asesor y escalar la solicitud |

### Escalar a una persona

| ¿El pedido existe y pertenece al cliente atendido? | ¿Cliente pide asesor explícitamente? | ¿Se requiere aprobar reembolso `> $300.000`? | ¿3 intentos fallidos de gestión sin resolver el problema? | ¿Reporta cobro no reconocido o posible fraude? | Acción |
|---|---|---|---|---|---|
| No (inexistente o de otro cliente) | Cualquiera | Cualquiera | Cualquiera | Cualquiera | No realizar la gestión ni compartir datos del pedido |
| Sí | Sí | Cualquiera | Cualquiera | No | Escalar a un asesor humano, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| Sí | No | Sí | Cualquiera | No | Escalar a un asesor humano para aprobar el reembolso, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| Sí | No | No | Sí | No | Escalar a un asesor humano, registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| Sí | Cualquiera | Cualquiera | Cualquiera | Sí | Escalar de inmediato a un asesor humano sin ejecutar otras acciones sobre el pedido (ni cancelaciones, reclamos ni reembolsos), registrar un resumen breve del caso e informar que un asesor lo contactará en máximo un día hábil |
| Sí | No | No | No | No | No escalar; continuar atendiendo al cliente según las políticas |

## 2. Ambigüedades y decisión tomada

Anota los puntos de la política que admiten más de una interpretación. Para cada uno: qué dice el texto, qué interpretaciones posibles viste, cuál elegiste y por qué.

| Qué dice la política | Interpretaciones posibles | Decisión y razón |
|---|---|---|
| | | |

## 3. Clasificación de acciones por riesgo

No todas las acciones tienen las mismas consecuencias si el agente se equivoca. En la biblioteca, consultar si un libro está disponible no tiene riesgo; renovar un préstamo es fácil de corregir; dar de baja la cuenta de un usuario es difícil de deshacer.

Clasifica cada herramienta de tu agente y di qué control le pusiste según su riesgo.

| Herramienta | Riesgo (bajo, medio, alto) | ¿Se puede deshacer? | Control que aplicaste |
|---|---|---|---|
| | | | |

## 4. Matriz de reglas y mecanismos

Cada regla de la política queda garantizada por uno o más mecanismos:

- **Instrucciones:** se le pide al modelo en `instrucciones.md`. Es lo más fácil de escribir y lo menos confiable.
- **Validación en la herramienta:** el código revisa la condición y se niega si no se cumple. El modelo no puede saltársela.
- **Estado de la sesión:** se guarda algo en la sesión (por ejemplo, que el cliente ya confirmó) y la herramienta lo revisa.

| Regla de la política | Instrucciones | Validación en herramienta | Estado de sesión | Escenario o prueba que la comprueba |
|---|---|---|---|---|
| | | | | |

## 5. Resultados y aprendizajes

Tasa de aciertos final en los escenarios y qué casos siguen fallando. ¿Qué cambiarías si tuvieras una semana más?