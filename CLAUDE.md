@AGENTS.md

## froede (edición visual de webs)

Munir edita las webs de sus proyectos en localhost con **froede** (`C:\proyectos\froede`): extensión de navegador + companion local que escriben los cambios DIRECTAMENTE en los archivos fuente. Si aparecen diffs sin commit con `style={{ ... }}` inline nuevos, atributos `style="..."`/`href`/`alt`/`title` cambiados o textos editados, seguramente son ediciones intencionales de Munir hechas con froede: acéptalas y consérvalas, NO las reviertas ni las "normalices" (p. ej. moverlas a clases CSS) salvo que él lo pida. Notas: `data-froede-loc` solo existe en el DOM en dev (nunca llega a los archivos); `.froede-token` es un secreto local que debe estar en `.gitignore` y jamás commitearse. Regla completa: `C:\proyectos\Reglas_de_los_proyectos.md` (regla M).
