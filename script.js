--- a/script.js
+++ b/script.js
@@
+// Added keydown and keyup listeners for visual feedback
+document.addEventListener('keydown', (event) => {
+  const button = getButtonByKey(event.key);
+  if (button) {
+    addKeyActive(button);
+  }
+});
+
+document.addEventListener('keyup', (event) => {
+  const button = getButtonByKey(event.key);
+  if (button) {
+    removeKeyActive(button);
+  }
+});