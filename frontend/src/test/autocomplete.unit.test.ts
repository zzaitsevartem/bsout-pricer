import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

import ts from 'typescript';
import { expect, it } from 'vitest';

const src = join(dirname(fileURLToPath(import.meta.url)), '..');

function applicationFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory())
      return entry.name === 'test' || entry.name === '__tests__' ? [] : applicationFiles(path);
    return entry.name.endsWith('.tsx') && !/\.(test|spec)\.tsx$/.test(entry.name) ? [path] : [];
  });
}

it('disables autocomplete on every native input and textarea', () => {
  const violations: string[] = [];
  let fields = 0;

  for (const path of applicationFiles(src)) {
    const source = ts.createSourceFile(
      path,
      readFileSync(path, 'utf8'),
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TSX,
    );
    function visit(node: ts.Node) {
      if (
        (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) &&
        (node.tagName.getText(source) === 'input' || node.tagName.getText(source) === 'textarea')
      ) {
        fields++;
        const props = node.attributes.properties;
        const index = props.findIndex(
          (prop) => ts.isJsxAttribute(prop) && prop.name.getText(source) === 'autoComplete',
        );
        const attribute = props[index];
        if (
          index < 0 ||
          !ts.isJsxAttribute(attribute) ||
          !attribute.initializer ||
          !ts.isStringLiteral(attribute.initializer) ||
          attribute.initializer.text !== 'off' ||
          props.slice(index + 1).some(ts.isJsxSpreadAttribute)
        ) {
          const line = source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1;
          violations.push(`${relative(src, path)}:${line}`);
        }
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
  }

  expect(fields).toBeGreaterThan(0);
  expect(
    violations,
    'Fields must end with an explicit autoComplete="off" after any prop spreads',
  ).toEqual([]);
});
