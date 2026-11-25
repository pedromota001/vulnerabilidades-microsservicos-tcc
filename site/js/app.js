/* Site de dados do TCC. Todo dado vem de data/dados.json (gerado da planilha). */
(function () {
  'use strict';
  var D, main = document.getElementById('conteudo');
  var idx = {};

  // ------------------------------------------------------------ utilidades
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function pct(a, b) { return (100 * a / b).toFixed(1).replace('.', ',') + '%'; }
  function porId(lista, chave) { var o = {}; lista.forEach(function (x) { o[x[chave]] = x; }); return o; }
  function linkVuln(id) { return '<a class="id" href="#/vulnerabilidade/' + esc(id) + '">' + esc(id) + '</a>'; }
  function linkMit(id) { return '<a class="id" href="#/mitigacao/' + esc(id) + '">' + esc(id) + '</a>'; }
  function linkEstudo(c) { return '<a class="id" href="#/estudos/' + esc(c) + '" title="' + esc(idx.estudos[c] ? idx.estudos[c].titulo : '') + '">' + esc(c) + '</a>'; }
  function etq(tipo) {
    var cls = tipo.split(' ')[0];
    return '<span class="etq ' + esc(cls) + '">' + esc(tipo) + '</span>';
  }
  function frenteLabel(nome) {
    var f = D.frentes.find(function (x) { return x.nome === nome; });
    return f && f.titulo ? nome + ' — ' + f.titulo : nome;
  }
  function instituicao() { return (D.sobre.instituicao.match(/\(([^)]+)\)/) || [])[1] || ''; }
  function rotuloTema() {
    var escuro = document.documentElement.dataset.theme === 'dark';
    document.querySelector('.tema-btn').textContent = escuro ? 'Modo claro' : 'Modo escuro';
  }
  function render(titulo, html) {
    main.innerHTML = html;
    document.title = titulo + ' · Vulnerabilidades em Microsserviços';
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }

  // ------------------------------------------------------------ páginas
  function inicio() {
    var i = D.indicadores, s = D.sobre;
    var kpi = function (n, t) { return '<div class="kpi"><b>' + esc(n) + '</b><span>' + esc(t) + '</span></div>'; };
    render('Início',
      '<p class="sobretitulo">' + esc(instituicao()) + '</p>' +
      '<h1>' + esc(s.titulo) + '</h1>' +
      '<p class="sub">' + esc(s.autor) + ' · Orientador: ' + esc(s.orientador) + '</p>' +
      '<p class="texto">' + esc(s.rastreabilidade) + '</p>' +
      '<div class="kpis">' +
        kpi(i.estudos, 'estudos selecionados') +
        kpi(i.vulnerabilidades, 'vulnerabilidades em ' + i.frentes + ' frentes e ' + i.categorias + ' categorias') +
        kpi(i.mitigacoes, 'mitigações no catálogo (' + i.mitigacoes_ligadas + ' ligadas a vulnerabilidades)') +
        kpi(pct(i.vulns_explicitas, i.vulnerabilidades), i.vulns_explicitas + ' de ' + i.vulnerabilidades + ' vulnerabilidades com mitigação explícita') +
        kpi(pct(i.vulns_sem_concreta, i.vulnerabilidades), i.vulns_sem_concreta + ' de ' + i.vulnerabilidades + ' sem mitigação concreta') +
        kpi(pct(i.matriz_principal, i.matriz_celulas), i.matriz_principal + ' de ' + i.matriz_celulas + ' células da matriz com evidência dos autores') +
      '</div>' +
      '<div class="botoes">' + arquivos() + '</div>' +
      '<h2>Do item extraído à vulnerabilidade</h2>' +
      '<div class="tabela-wrap"><table><tbody>' +
        '<tr><td>Itens registrados nos documentos de extração</td><td class="num">' + i.itens_extraidos + '</td></tr>' +
        '<tr><td>Itens que não viraram vulnerabilidade (contexto, fora do escopo etc.)</td><td class="num">' + i.itens_nao_contados + '</td></tr>' +
        '<tr><td>Itens que sustentam vulnerabilidades</td><td class="num">' + i.itens_contados + '</td></tr>' +
        '<tr><td>Linhas de codificação (com ' + i.desdobramentos + ' desdobramentos)</td><td class="num">' + i.linhas_codificacao + '</td></tr>' +
        '<tr><td>Vulnerabilidades consolidadas</td><td class="num">' + i.vulnerabilidades + '</td></tr>' +
      '</tbody></table></div>');
  }

  function arquivos() {
    var h = '';
    if (D.arquivos.pdf) h += '<a class="botao" href="' + esc(D.arquivos.pdf) + '">Ler o TCC (PDF)</a>';
    h += '<a class="botao' + (D.arquivos.pdf ? ' sec' : '') + '" href="' + esc(D.arquivos.planilha) + '" download>Baixar a planilha de análise (.xlsx)</a>';
    if (D.sobre.repositorio) h += '<a class="botao sec" href="' + esc(D.sobre.repositorio) + '">Repositório no GitHub</a>';
    return h;
  }

  function taxonomia() {
    var h = '<h1>Taxonomia</h1><p class="sub">' + esc(D.sobre.estrutura) + '</p><div class="arvore">';
    D.frentes.forEach(function (f) {
      var n = f.categorias.reduce(function (a, c) { return a + c.vulns.length; }, 0);
      h += '<details open><summary>' + esc(frenteLabel(f.nome)) + ' <span class="contagem">(' + f.categorias.length + ' categorias, ' + n + ' vulnerabilidades)</span></summary>';
      if (f.descricao) h += '<p class="descr-frente">' + esc(f.descricao) + '</p>';
      f.categorias.forEach(function (c) {
        h += '<details><summary>' + esc(c.nome) + ' <span class="contagem">(' + c.vulns.length + ')</span></summary><ul>';
        c.vulns.forEach(function (id) {
          var v = idx.vulns[id];
          h += '<li>' + linkVuln(id) + ' ' + esc(v.nome) + ' <span class="contagem">· ' + v.n_estudos + ' estudo(s)</span></li>';
        });
        h += '</ul></details>';
      });
      h += '</details>';
    });
    render('Taxonomia', h + '</div>');
  }

  function opcoes(valores, todos) {
    return '<option value="">' + todos + '</option>' + valores.map(function (v) {
      return '<option value="' + esc(v[0]) + '">' + esc(v[1]) + '</option>';
    }).join('');
  }

  function vulnerabilidades() {
    var cats = [];
    D.frentes.forEach(function (f) { f.categorias.forEach(function (c) { cats.push([c.nome, c.nome]); }); });
    var maxN = Math.max.apply(null, D.vulnerabilidades.map(function (v) { return v.n_estudos; }));
    var ns = []; for (var k = 1; k <= maxN; k++) ns.push([k, 'ao menos ' + k]);
    render('Vulnerabilidades',
      '<h1>Vulnerabilidades</h1><p class="sub">' + D.vulnerabilidades.length + ' vulnerabilidades consolidadas. Cada uma é classificada pela ligação mais forte com uma mitigação (ordem: ' + esc(D.ordem_ligacao.join(', ')) + ').</p>' +
      '<div class="filtros" role="search">' +
        '<label>Buscar<input id="f-busca" type="search" placeholder="ID, nome ou descrição"></label>' +
        '<label>Frente<select id="f-frente">' + opcoes(D.frentes.map(function (f) { return [f.nome, frenteLabel(f.nome)]; }), 'Todas') + '</select></label>' +
        '<label>Categoria<select id="f-cat">' + opcoes(cats, 'Todas') + '</select></label>' +
        '<label>Nº de estudos<select id="f-n">' + opcoes(ns, 'Qualquer') + '</select></label>' +
        '<label>Ligação mais forte<select id="f-lig">' + opcoes(D.ordem_ligacao.map(function (t) { return [t, t]; }), 'Qualquer') + '</select></label>' +
      '</div><p class="contador" id="contador" aria-live="polite"></p>' +
      '<div class="tabela-wrap"><table><thead><tr><th>ID</th><th>Vulnerabilidade</th><th>Categoria</th><th class="num">Estudos</th><th class="num">Mitigações</th><th>Ligação mais forte</th></tr></thead><tbody id="tb"></tbody></table></div>');
    var el = function (id) { return document.getElementById(id); };
    function filtrar() {
      var q = el('f-busca').value.trim().toLowerCase(), fr = el('f-frente').value, ca = el('f-cat').value,
        n = +el('f-n').value || 0, li = el('f-lig').value;
      var lst = D.vulnerabilidades.filter(function (v) {
        return (!q || (v.id + ' ' + v.nome + ' ' + v.descricao).toLowerCase().indexOf(q) >= 0) &&
          (!fr || v.frente === fr) && (!ca || v.categoria === ca) && v.n_estudos >= n && (!li || v.ligacao_mais_forte === li);
      });
      el('tb').innerHTML = lst.map(function (v) {
        return '<tr><td>' + linkVuln(v.id) + '</td><td><a href="#/vulnerabilidade/' + esc(v.id) + '">' + esc(v.nome) + '</a></td><td>' + esc(v.categoria) +
          '</td><td class="num">' + v.n_estudos + '</td><td class="num">' + v.ligacoes.length + '</td><td>' + etq(v.ligacao_mais_forte) + '</td></tr>';
      }).join('') || '<tr><td colspan="6">Nenhuma vulnerabilidade com esses filtros.</td></tr>';
      el('contador').textContent = lst.length + ' de ' + D.vulnerabilidades.length + ' vulnerabilidades';
    }
    ['f-busca', 'f-frente', 'f-cat', 'f-n', 'f-lig'].forEach(function (id) { el(id).addEventListener('input', filtrar); });
    filtrar();
  }

  function vulnerabilidade(id) {
    var v = idx.vulns[id];
    if (!v) return naoEncontrado();
    var origens = D.ocorrencias_vuln.filter(function (o) { return o.destino === id; });
    render(v.id + ' ' + v.nome,
      '<a class="voltar" href="#/vulnerabilidades">← Todas as vulnerabilidades</a>' +
      '<p class="trilha">' + esc(frenteLabel(v.frente)) + ' › ' + esc(v.categoria) + '</p>' +
      '<h1><span class="id">' + esc(v.id) + '</span> ' + esc(v.nome) + '</h1>' +
      '<p class="texto">' + esc(v.descricao) + '</p>' +
      (v.observacao ? '<div class="cartao"><b>Observação da análise:</b> ' + esc(v.observacao) + '</div>' : '') +
      '<h2>Estudos que a sustentam (' + v.lista_estudos.length + ')</h2><p>' + v.lista_estudos.map(linkEstudo).join(', ') + '</p>' +
      '<h2>Mitigações ligadas (' + v.ligacoes.length + ')</h2>' +
      (v.ligacoes.length ? '<div class="tabela-wrap"><table><thead><tr><th>ID</th><th>Mitigação</th><th>Tipo de ligação</th><th>Base da ligação</th></tr></thead><tbody>' +
        v.ligacoes.map(function (l) {
          return '<tr><td>' + linkMit(l.mitigacao) + '</td><td>' + esc(idx.mits[l.mitigacao].nome) + '</td><td>' + etq(l.tipo) + '</td><td>' + esc(l.base) + '</td></tr>';
        }).join('') + '</tbody></table></div>' : '<p>Nenhuma mitigação ligada.</p>') +
      '<h2>Itens de extração de origem (' + origens.length + ')</h2>' +
      '<ul class="lista-trechos">' + origens.map(function (o) {
        return '<li>' + esc(o.item) + '<div class="meta">' + linkEstudo(o.estudo) + ', ' + esc(o.pagina) + ' · registro ' + esc(o.id) + '</div></li>';
      }).join('') + '</ul>');
  }

  function mitigacoes() {
    render('Mitigações',
      '<h1>Mitigações</h1><p class="sub">Catálogo de ' + D.mitigacoes.length + ' mitigações; ' + D.indicadores.mitigacoes_ligadas + ' estão ligadas a ao menos uma vulnerabilidade.</p>' +
      '<div class="filtros"><label>Buscar<input id="m-busca" type="search" placeholder="ID, nome ou descrição"></label></div>' +
      '<div class="tabela-wrap"><table><thead><tr><th>ID</th><th>Mitigação</th><th>Descrição</th><th class="num">Estudos</th><th class="num">Vulnerabilidades</th></tr></thead><tbody id="tb"></tbody></table></div>');
    var tb = document.getElementById('tb'), busca = document.getElementById('m-busca');
    function f() {
      var q = busca.value.trim().toLowerCase();
      tb.innerHTML = D.mitigacoes.filter(function (m) { return !q || (m.id + ' ' + m.nome + ' ' + m.descricao).toLowerCase().indexOf(q) >= 0; })
        .map(function (m) {
          return '<tr><td>' + linkMit(m.id) + '</td><td><a href="#/mitigacao/' + esc(m.id) + '">' + esc(m.nome) + '</a></td><td>' + esc(m.descricao) +
            '</td><td class="num">' + m.n_estudos + '</td><td class="num">' + m.n_vulns + '</td></tr>';
        }).join('') || '<tr><td colspan="5">Nenhuma mitigação encontrada.</td></tr>';
    }
    busca.addEventListener('input', f); f();
  }

  function mitigacao(id) {
    var m = idx.mits[id];
    if (!m) return naoEncontrado();
    var oc = D.ocorrencias_mit.filter(function (o) { return o.mitigacao === id; });
    var lin = D.matriz.find(function (x) { return x.mitigacao === id; });
    render(m.id + ' ' + m.nome,
      '<a class="voltar" href="#/mitigacoes">← Todas as mitigações</a>' +
      '<h1><span class="id">' + esc(m.id) + '</span> ' + esc(m.nome) + '</h1><p class="texto">' + esc(m.descricao) + '</p>' +
      '<h2>Estudos que a citam (' + m.lista_estudos.length + ')</h2><p>' + (m.lista_estudos.map(linkEstudo).join(', ') || '—') + '</p>' +
      '<h2>Vulnerabilidades ligadas (' + m.ligacoes.length + ')</h2>' +
      (m.ligacoes.length ? '<div class="tabela-wrap"><table><thead><tr><th>ID</th><th>Vulnerabilidade</th><th>Tipo de ligação</th><th>Base da ligação</th></tr></thead><tbody>' +
        m.ligacoes.map(function (l) {
          return '<tr><td>' + linkVuln(l.vuln) + '</td><td>' + esc(idx.vulns[l.vuln].nome) + '</td><td>' + etq(l.tipo) + '</td><td>' + esc(l.base) + '</td></tr>';
        }).join('') + '</tbody></table></div>' : '<p>Não está ligada a nenhuma vulnerabilidade.</p>') +
      (lin ? '<h2>Trade-offs</h2><p><a href="#/matriz/' + esc(id) + '">Ver esta mitigação na matriz de trade-offs</a></p>' : '') +
      '<h2>Menções nos estudos (' + oc.length + ')</h2><ul class="lista-trechos">' + oc.map(function (o) {
        return '<li>' + esc(o.trecho) + '<div class="meta">' + linkEstudo(o.estudo) + ', ' + esc(o.pagina) + ' · registro ' + esc(o.id) + '</div></li>';
      }).join('') + '</ul>');
  }

  function matriz(sel) {
    var leg = Object.keys(D.niveis).map(function (n) { return '<span style="background:' + esc(D.niveis[n]) + '">' + esc(n) + '</span>'; }).join('') +
      '<span class="vazio">Sem evidência</span>';
    var h = '<h1>Matriz de trade-offs</h1><p class="sub">' + D.matriz.length + ' mitigações × ' + D.dimensoes.length + ' dimensões (' + esc(D.dimensoes.join(', ').toLowerCase()) +
      '). ' + D.indicadores.matriz_sem_evidencia + ' das ' + D.indicadores.matriz_celulas + ' células não têm evidência. Selecione uma célula para ver a observação e os trechos que a sustentam.</p>' +
      '<div class="legenda" aria-label="Legenda dos níveis"><b>Legenda:</b>' + leg + '</div>' +
      '<div class="tabela-wrap"><table class="matriz"><thead><tr><th>Mitigação</th>' +
      D.dimensoes.map(function (d) { return '<th scope="col">' + esc(d) + '</th>'; }).join('') + '</tr></thead><tbody>';
    D.matriz.forEach(function (lin) {
      h += '<tr><th scope="row" style="white-space:normal;font-weight:400">' + linkMit(lin.mitigacao) + ' ' + esc(lin.nome) + '</th>';
      lin.celulas.forEach(function (c, i) {
        var vazio = c.nivel === 'Sem evidência', cor = D.niveis[c.nivel];
        h += '<td class="cel"><button type="button" class="cel-btn' + (vazio ? ' vazio' : '') + '" data-m="' + esc(lin.mitigacao) + '" data-d="' + i + '"' +
          (cor ? ' style="--cor:' + esc(cor) + '"' : '') + ' aria-pressed="false" aria-label="' + esc(lin.mitigacao + ', ' + c.dimensao + ': ' + c.nivel) + '">' +
          '<span>' + esc(c.nivel) + '</span>' + (vazio ? '' : '<small>' + esc(c.base) + ' · ' + c.n_estudos + ' estudo(s)</small>') + '</button></td>';
      });
      h += '</tr>';
    });
    h += '</tbody></table></div><p class="meta">' + esc(D.legenda_matriz) + '</p><section id="painel-celula" class="cartao" aria-live="polite" tabindex="-1"></section>';
    render('Matriz de trade-offs', h);
    var painel = document.getElementById('painel-celula');
    function mostrar(btn) {
      main.querySelectorAll('.cel-btn[aria-pressed="true"]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      btn.setAttribute('aria-pressed', 'true');
      var m = btn.dataset.m, c = D.matriz.find(function (x) { return x.mitigacao === m; }).celulas[+btn.dataset.d];
      var tr = D.trechos.filter(function (t) { return t.mitigacao === m && t.dimensao === c.dimensao; });
      painel.innerHTML = '<h2 style="margin-top:0">' + esc(m + ' ' + idx.mits[m].nome) + ' — ' + esc(c.dimensao) + '</h2>' +
        '<p><b>Nível:</b> ' + esc(c.nivel) + (c.base && c.base !== '—' ? ' · <b>Base:</b> ' + esc(c.base) : '') + ' · <b>Estudos:</b> ' + esc(c.n_estudos) + '</p>' +
        (c.observacao ? '<p>' + esc(c.observacao) + '</p>' : '') +
        '<h3>Trechos (' + tr.length + ')</h3>' + (tr.length ? '<ul class="lista-trechos">' + tr.map(function (t) {
          return '<li>' + esc(t.texto) + (t.caracteristica ? '<div><b>Característica:</b> ' + esc(t.caracteristica) + '</div>' : '') +
            '<div class="meta">' + linkEstudo(t.estudo) + ', ' + esc(t.pagina) + ' · ' + esc(t.evidencia) + ' · mapeamento ' + esc(t.mapeamento.toLowerCase()) +
            ' · destino ' + esc(t.destino) + ' · registro ' + esc(t.id) + '</div>' +
            (t.justificativa ? '<div class="meta">Justificativa do mapeamento: ' + esc(t.justificativa) + '</div>' : '') + '</li>';
        }).join('') + '</ul>' : '<p>Nenhum trecho registrado para esta célula.</p>');
      painel.focus();
    }
    main.querySelectorAll('.cel-btn').forEach(function (b) { b.addEventListener('click', function () { mostrar(b); }); });
    if (sel) { var b = main.querySelector('.cel-btn[data-m="' + sel + '"]:not(.vazio)') || main.querySelector('.cel-btn[data-m="' + sel + '"]'); if (b) { b.scrollIntoView({ block: 'center' }); mostrar(b); } }
  }

  function estudos(sel) {
    render('Estudos',
      '<h1>Estudos selecionados</h1><p class="sub">Os ' + D.estudos.length + ' estudos do corpus, identificados por códigos de três letras.</p>' +
      '<div class="tabela-wrap"><table><thead><tr><th>Código</th><th>Título</th><th>Autores</th><th class="num">Ano</th><th>Veículo</th><th>Tipo</th><th>Nível</th><th>DOI</th></tr></thead><tbody>' +
      D.estudos.map(function (e) {
        return '<tr id="estudo-' + esc(e.codigo) + '"><td class="id">' + esc(e.codigo) + '</td><td>' + esc(e.titulo) + '</td><td>' + esc(e.autores) + '</td><td class="num">' + esc(e.ano) +
          '</td><td>' + esc(e.veiculo) + '</td><td>' + esc(e.tipo) + '</td><td>' + esc(e.nivel) + '</td><td>' +
          (e.doi ? '<a href="https://doi.org/' + esc(e.doi) + '" rel="noopener">' + esc(e.doi) + '</a>' : '—') + '</td></tr>';
      }).join('') + '</tbody></table></div>');
    if (sel) { var r = document.getElementById('estudo-' + sel); if (r) { r.scrollIntoView({ block: 'center' }); r.style.outline = '3px solid var(--foco)'; } }
  }

  function sobre() {
    var s = D.sobre;
    var ano = (s.versao.match(/\b(\d{4})\b/) || [])[1] || '';
    var partes = s.autor.split(' '), sobren = partes.pop();
    var inst = (s.instituicao.match(/\(([^)]+)\)/) || [])[1] || '';
    var cit = esc(sobren.toUpperCase() + ', ' + partes.join(' ')) + '. <b>' + esc(s.titulo) + '</b>. ' + esc(ano) + '. ' + esc(inst) + '.';
    render('Sobre',
      '<h1>Sobre</h1><div class="texto">' +
      '<p><b>Trabalho:</b> ' + esc(s.titulo) + '</p><p><b>Autor:</b> ' + esc(s.autor) + '<br><b>Orientador:</b> ' + esc(s.orientador) + '</p><p>' + esc(inst) + '</p>' +
      '<h2>Como citar</h2><div class="cartao citacao">' + cit + '</div>' +
      '<h2>Licença</h2><p>' + (s.licenca ? esc(s.licenca) : 'Consulte o repositório.') + '</p>' +
      '<h2>Método, em resumo</h2><p>' + esc(s.escopo.replace(/^•\s*/, '')) + '</p><p>' + esc(s.estrutura) + '</p>' +
      '<p>Regras de contagem:</p><ol>' + s.regras_contagem.map(function (r) { return '<li>' + esc(r.replace(/^\d+\.\s*/, '')) + '</li>'; }).join('') + '</ol>' +
      '<p><b>Tipos de ligação entre vulnerabilidade e mitigação:</b></p><ul>' + Object.keys(D.tipos_ligacao).map(function (t) { return '<li>' + etq(t) + ' ' + esc(D.tipos_ligacao[t]) + '</li>'; }).join('') + '</ul>' +
      '<p>' + esc(s.paginas.replace(/^•\s*/, '')) + '</p>' +
      '<h2>Material completo</h2><p>Este site mostra os resultados. O registro completo da análise (decisões, regras, seleção dos candidatos, itens fora do escopo, contexto e lacunas, contagens detalhadas) está na planilha.</p>' +
      '<div class="botoes">' + arquivos() + '</div></div>');
  }

  function naoEncontrado() { render('Não encontrado', '<h1>Página não encontrada</h1><p><a href="#/">Voltar ao início</a></p>'); }

  // ------------------------------------------------------------ roteador
  var rotas = {
    '': inicio, taxonomia: taxonomia, vulnerabilidades: vulnerabilidades, vulnerabilidade: vulnerabilidade,
    mitigacoes: mitigacoes, mitigacao: mitigacao, matriz: matriz, estudos: estudos, sobre: sobre
  };
  function rotear() {
    var p = location.hash.replace(/^#\/?/, '').split('/').map(decodeURIComponent);
    var fn = rotas[p[0]] || naoEncontrado;
    var secao = { vulnerabilidade: 'vulnerabilidades', mitigacao: 'mitigacoes' }[p[0]] || p[0];
    document.querySelectorAll('nav a').forEach(function (a) {
      if (a.getAttribute('href') === '#/' + secao) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    document.getElementById('nav').classList.remove('aberto');
    document.querySelector('.menu-btn').setAttribute('aria-expanded', 'false');
    fn(p[1]);
  }

  // ------------------------------------------------------------ interface
  document.querySelector('.menu-btn').addEventListener('click', function () {
    var n = document.getElementById('nav'), aberto = n.classList.toggle('aberto');
    this.setAttribute('aria-expanded', String(aberto));
  });
  document.querySelector('.tema-btn').addEventListener('click', function () {
    var novo = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = novo;
    try { localStorage.setItem('tema', novo); } catch (e) {}
    rotuloTema();
  });

  fetch('data/dados.json').then(function (r) { return r.json(); }).then(function (d) {
    D = d;
    rotuloTema();
    document.getElementById('marca-sub').textContent = instituicao().split(',')[0];
    idx.vulns = porId(D.vulnerabilidades, 'id');
    idx.mits = porId(D.mitigacoes, 'id');
    idx.estudos = porId(D.estudos, 'codigo');
    document.getElementById('rodape').innerHTML = esc(D.sobre.autor) + ' · ' + esc((D.sobre.instituicao.match(/\(([^)]+)\)/) || [])[1] || '') +
      '<br>Todos os dados deste site são gerados a partir da planilha de análise. <a href="' + esc(D.arquivos.planilha) + '" download>Baixar a planilha</a>.';
    window.addEventListener('hashchange', rotear);
    rotear();
  }).catch(function () {
    main.innerHTML = '<p>Não foi possível carregar os dados.</p>';
  });
})();
