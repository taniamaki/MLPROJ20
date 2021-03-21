
from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
from datetime import date, datetime, timedelta
import pandas as pd
import requests
import time
                                                                               
def getPages(url):
    """
    Função usada para pegar um objeto BeautifulSoup dada uma URL
    Entrada: url
    Retorno: Objeto Beautiful Soup
    """
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    
    try:
        req = session.get(url, headers=headers)
    except requests.exceptions.RequestException:
        return None
    bs = BeautifulSoup(req.text, 'html.parser')
    return bs

def getLinksPauta(url):
    """ 
    Captura das URLs das Pautas 
    In: URL 
    Out: List urls das pautas
    """
    links = []
    link = url
    for i in range(5):
        try:
            bs = getPages(link)
        except HTTPError as e:
            return None
        try:
            div_anterior = bs.find(class_ = 'span12 text-center')
            link_anterior = div_anterior.findAll('a')
        except AttributeError as e:
            return None
        links.append(link_anterior[0].get('href'))
        link = link_anterior[0].get('href')
    return links

def getLinkPag(url):
    """ 
    Captura das URLs das Páginas 
    In: URL 
    Out: List urls das páginas
    """
    link = []
    bs = getPages(url)
    pag = bs.findAll(class_ = 'pagination-list__number-link')
    #print(pag)
    for p in pag:
        link.append(p.get('href'))
        #print(p.get('href'))
    link[0]=(url)
    return link


def getLinkAgenda(url):
    """ 
    Captura das URLs das Agendas 
    In: URL 
    Out: List urls das pautas
    """
    links = []
    for u in url:
        try:
            bs = getPages(u)
        except HTTPError as e:
            return None
        cl = bs.findAll(class_ = 'g-agenda__nome')
        for c in cl:
            #print(c.get('href'))
            links.append(c.get('href'))

        #separar links de cada casa
        link_camara = []

        for l in links:
            if l.startswith('https://www.camara.leg.br/evento-legislativo/'):
                link_camara.append(l) 
        return link_camara


def getLinkComissoes(url):
    links = []
    try:
        bs = getPages(url)
    except HTTPError as e:
        return None
    try:
        cl = bs.findAll('div', {'class':'cn-agenda-casas-tabela-celula'})
    except AttributeError as e:
        return None
    for c in cl:
        link = c.find('a')
        if link is not None:
            l = link.get('href')
            if l.startswith('https://legis.senado.leg.br/comissoes/reuniao'):
                links.append(l)
    return links

def getLinkNotasSenado(linksPauta):
    linksNotas = []
    for l in linksPauta:
        try:
            bs = getPages(l)
        except HTTPError as e:
            return None
        try:
            div_links = bs.find(class_ = 'botoes row-fluid')
            link = div_links.findAll('a')  
            #print(link) 
        except AttributeError as e:
            return None
        else: 
            if link[0].get('href').startswith('https://www25.senado.leg.br'):
                #print(link[0].get('href'))
                linksNotas.append(link[0].get('href'))
    return linksNotas

def getLinkNotasCongresso(links):
    congresso = []
    for l in links:
        try:
            bs = getPages(l)
        except HTTPError as e:
            return None
        try:
            cl = bs.findAll('div', {'class':'pull-right v-img icone-info bgc-temporaria'})
        except AttributeError as e:
            return None
        for c in cl:
            link = c.find('a')
            if link is not None:
                l = link.get('href')
                if l.startswith('http://www25.senado.leg.br/web/atividade/notas-taquigraficas'):
                    congresso.append(l)
    return congresso

def getIntegraTexto(link_camara):
    txt_links = [] #recebe o link para notas taquigráficas
    for l in link_camara:
        if l not in('https://escriba.camara.leg.br/escriba-servicosweb/html/60521'):
            try:
                bs = getPages(l)
            except HTTPError as e:
                return None
            time.sleep(5)
            try:
                a = bs.find('a', {'class':"links-adicionais__link-icone links-adicionais__link-icone--dialogo"})
            except AttributeError as e:
                return None
            if a is not None:
                txt_links.append(a.get('href'))
                #print(a.get('href'))
        return txt_links
        
def getPronunciamentoSenado(linkNotas):
    pronunciamento = []
    for l in linkNotas:
        try:
            bs = getPages(l)
        except HTTPError as e:
            return None
        try: 
            txt = bs.findAll('div', {'class':'principalStyle'})
        except AttributeError as e:
            return None

        #cabecalho
        cabecalho = bs.find('div', {'class':'container-fluid'})
        cab = cabecalho.p.find_next('p').get_text()

        #max indice bold - maior linha que contenha parâmetro em negrito
        i_bold = []
        for i in range(0, len(txt)):
            if txt[i].b is not None:
                i_bold.append(i)
        max_bold = max(i_bold)

        #Agrupar fala do indivíduo
        pron = []
        for i in range(0, max_bold):
            aux = []
            if txt[i].b is not None:
                aux.append(txt[i].get_text())
                j = 1
                while txt[i + j].b is None:
                    aux.append(txt[i + j].get_text())
                    j += 1
                pron.append(aux)     

        #unificar os itens de um bloco de fala
        for p in pron:
            separator = ' '
            pronunciamento.append([l, cab, separator.join(p)])
            #print([l, cab, separator.join(p)])
    return pronunciamento

def getPronunciamentoCamara(txt_links):
    pronunciamento = []

    for l in txt_links:
        if l.startswith('https://escriba.camara.leg.br/escriba-servicosweb/html/'):
            try:
                bs = getPages(l)
            except HTTPError as e:
                return None  
            try:
                txt = bs.findAll('div', {'class':'principalStyle'})
            except AttributeError as e:
                return None
            
            try:
                titulo = bs.find('div', {'class':"contentTitle"})
            except AttributeError as e:
                return None
            else:
                if titulo is not None:
                    titulo = titulo.get_text()

                #maior linha em negrito
                i_bold = []
                for i in range(0, len(txt)):
                    try:
                        txt[i].b
                    except AttributeError as e:
                        return None
                    else: 
                        if txt[i].b is not None:
                            i_bold.append(i)
                        max_bold = max(i_bold)  

                #Agrupar pronunciamento
                pron = []
                for i in range(max_bold):
                    aux = []
                    try:
                        txt[i].b
                    except AttributeError as e:
                        return None
                    else: 
                        if txt[i].b is not None:
                            aux.append(txt[i].get_text())
                            j = 1
                            while txt[i + j].b is None:
                                aux.append(txt[i + j].get_text())
                                j += 1
                            pron.append(aux)

                #juntar as linhas de um pronunciamento
                for p in pron:    
                    separator = ' '
                    pronunciamento.append([l, titulo, separator.join(p)])
    return pronunciamento

def getPronunciamentoCongresso(linkNotas):
    pronunciamento = []
    for l in linkNotas:
        try:
            bs = getPages(l)
        except HTTPError as e:
            return None
        try: 
            txt = bs.findAll('div', {'class':'principalStyle'})
        except AttributeError as e:
            return None

        #cabecalho
        cabecalho = bs.findAll('h1')
        cab = cabecalho[1].get_text()

        #max indice bold - maior linha que contenha parâmetro em negrito
        i_bold = []
        for i in range(0, len(txt)):
            if txt[i].b is not None:
                i_bold.append(i)
        max_bold = max(i_bold)

        #Agrupar fala do indivíduo
        pron = []
        for i in range(0, max_bold):
            aux = []
            if txt[i].b is not None:
                aux.append(txt[i].get_text())
                j = 1
                while txt[i + j].b is None:
                    aux.append(txt[i + j].get_text())
                    j += 1
                pron.append(aux)     

        #unificar os itens de um bloco de fala
        for p in pron:
            separator = ' '
            pronunciamento.append([l, cab, separator.join(p)])
            #print([l, cab, separator.join(p)])
    return pronunciamento

def getCitacao(df):
    df['IN_BB'] = df['TXT'].str.contains("Banco do Brasil|Banco Público|Bancos Públicos|Bancos Oficiais|Banco Oficial|Bancos Federais|Banco Federal|Banco Federal|Instituição Financeira Pública|Instituições Financeiras Públicas|Instituição Financeira Oficial|Instituições Financeiras Oficiais", case=False, regex=True) 
    citacao =  df[df['IN_BB'] ==  True]
    return citacao


def main():
    #Senado
    
    senado = 'https://www25.senado.leg.br/web/atividade/sessao-plenaria'
    links_pauta = getLinksPauta(senado)
    #print(links_pauta)
    link_notas = getLinkNotasSenado(links_pauta)
    df_senado = pd.DataFrame(data=getPronunciamentoSenado(link_notas), columns=['LINK','CABECALHO','TXT'])
    df_senado_true = getCitacao(df_senado)
    #print(df_senado)
   

    #Camara

    dt_ini = date.today() - timedelta(days=5)
    dt_fim = date.today() 
    camara = 'https://www.camara.leg.br/agenda?termo=&dataviInicial__proxy={}%2F{}%2F{}&dataInicial={}%2F{}%2F{}&dataFinal__proxy={}%2F{}%2F{}&dataFinal={}%2F{}%2F{}'.format(dt_ini.day, dt_ini.month, dt_ini.year, dt_ini.day, dt_ini.month, dt_ini.year, dt_fim.day, dt_fim.month, dt_fim.year, dt_fim.day, dt_fim.month, dt_fim.year)
    paginas = getLinkPag(camara)
    integra_texto = (getLinkAgenda(paginas))
    #print(integra_texto)
    txt_links = getIntegraTexto(integra_texto)
    df_camara =  pd.DataFrame(data=getPronunciamentoCamara(txt_links), columns=['LINK','CABECALHO','TXT'])
    df_camara_true = getCitacao(df_camara)
    #print(df_camara_True)

    #Congresso
   
    congresso = 'https://www.congressonacional.leg.br/sessoes/agenda-do-congresso-nacional'
    link_pauta = getLinksPauta(congresso)
    link_notas_senado = getLinkNotasSenado(link_pauta)
    df_congresso = pd.DataFrame(data=getPronunciamentoSenado(link_notas_senado), columns=['LINK','CABECALHO','TXT'])
    df_congresso_true = getCitacao(df_congresso)
    #print(df_congresso_true)
 

    #Congresso comissoes
    congresso_agenda = 'https://www.congressonacional.leg.br/sessoes/agenda-do-congresso-senado-e-camara'
    link_comissoes = getLinkComissoes(congresso_agenda)
    link_notas_comissoes = getLinkNotasCongresso(link_comissoes)
    df_comissoes = pd.DataFrame(data=getPronunciamentoCongresso(link_notas_comissoes), columns=['LINK','CABECALHO','TXT'])
    df_comissoes_true = getCitacao(df_comissoes)


    #concatenate dataframes
    df_pronunciamento = df_senado.append(df_camara).append(df_congresso).append(df_comissoes)
    df_citacao = df_senado_true.append(df_camara_true).append(df_congresso_true).append(df_comissoes_true)

    #to csv
    df_pronunciamento.to_csv('Pronunciamento-{}.csv'.format(date.today() ))
    df_citacao.to_csv('InteresseBB-{}.csv'.format(date.today() ))

if __name__ =='__main__':
    main()