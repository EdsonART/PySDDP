import os
from typing import IO
import pandas as pd
import numpy as np

from PySDDP.newave.script.templates.ree import ReeTemplate


class Ree(ReeTemplate):

    def __init__(self):
        super().__init__()

        self.dir_base = None
        self.nome_arquivo = None
        self.numero_rees = None
        self.ree = dict()

    def ler(self, file_name: str, confhd) -> None:
        """
        Implementa o método para leitura do arquivo REE.DAT que contem os reservatórios equivalentes de energia
         que utilizados para a execucao do NEWAVE

        :param file_name: string com o caminho completo para o arquivo,
               confhd: classe contendo a configuracao de todas as usinas hidreletrica pertencentes ao estudo,
        """

        self.dir_base = os.path.split(file_name)[0]
        self.nome_arquivo = os.path.split(file_name)[1]
        self.numero_rees = 0

        # listas referentes ao dicionário REE
        self.ree['codigo'] = list()
        self.ree['nome'] = list()
        self.ree['submercado'] = list()
        self.ree['mes'] = list()
        self.ree['ano'] = list()
        self.ree['earmax'] = list()
        self.ree['ena_bruta'] = list()
        self.ree['ec'] = list()
        self.ree['efio_bruta'] = list()

        try:

            with open(file_name, 'r', encoding='latin-1') as f:  # type: IO[str]

                self.next_line(f)   # Linha de cabeçalho
                self.next_line(f)   # Linha de cabeçalho
                self.next_line(f)   # Linha de cabeçalho

                self.next_line(f)

                linha = self.linha

                #
                # Lê bloco 1
                #

                while linha[1:4] != '999':
                    #
                    # Incrementa contador de reservatórios equivalentes
                    #
                    self.numero_rees += 1

                    # Le_conteudo das linhas
                    codigo = int(linha[1:4])
                    nome = linha[5:15]
                    submercado = int(linha[18:21])
                    if len(linha) >= 25 and linha[23:25] != '  ':
                        mes = int(linha[23:25])
                    else:
                        mes = 0
                    if len(linha) >= 30 and linha[26:30] != '    ':
                        ano = int(linha[26:30])
                    else:
                        ano = 0
                    #
                    # Acrescenta dados lidos no banco de dados
                    #
                    self.ree['codigo'].append(codigo)
                    self.ree['nome'].append(nome)
                    self.ree['submercado'].append(submercado)
                    self.ree['mes'].append(mes)
                    self.ree['ano'].append(ano)
                    earmax = self._calc_earm_max(confhd,codigo)
                    [ena, ec, efio] = self._calc_ena(confhd, codigo)
                    self.ree['earmax'].append(earmax)
                    self.ree['ena_bruta'].append(ena)
                    self.ree['ec'].append(ec)
                    self.ree['efio_bruta'].append(efio)
                    #
                    # Lê próxima linha
                    #
                    self.next_line(f)
                    linha = self.linha

                #
                #  Lê bloco 2
                #

                self.bloco_ficticias['flag'] = 0

                self.next_line(f)
                linha = self.linha

                if len(linha) >= 25:
                    if linha[21:25] != '    ':
                        self.bloco_ficticias['flag'] = int(linha[21:25])

                self.next_line(f)
                linha = self.linha

        except Exception as err:
            if isinstance(err, StopIteration):
                self.bloco_ree['df'] = pd.DataFrame(self.ree, columns = [ 'codigo',
                                                                          'nome',
                                                                          'submercado',
                                                                          'mes',
                                                                          'ano',
                                                                          'earmax',
                                                                          'ena_bruta',
                                                                          'ec',
                                                                          'efio_bruta'] )

                print('OK! Leitura do', self.nome_arquivo ,'realizada com sucesso. (', self.numero_rees,
                      'Reservatórios Equivalentes de Energia Foram Lidos )')
            else:
                raise

        return

    def escrever(self, file_out: str) -> None:

        df = self.bloco_ree['df']

        try:
            with open(file_out, 'w', encoding='latin-1') as f:  # type: IO[str]

                f.write(" REES X SUBMERCADOS\n" )
                f.write(" NUM|NOME REES.| SUBM\n" )
                f.write(" XXX|XXXXXXXXXX|  XXX\n")

                tamanho = df.shape
                tamanho = tamanho[0]

                linha = 0

                conta_ree = 0

                while linha < tamanho:

                    registro = df.iloc[linha].values

                    if registro[3] > 0:
                        row = dict(
                                    codigo = registro[0],
                                    nome = registro[1],
                                    submercado = registro[2],
                                    mes = registro[3],
                                    ano = registro[4]
                                  )
                        formato = self.bloco_ree['formatoA']
                    else:
                        row = dict(
                                    codigo = registro[0],
                                    nome = registro[1],
                                    submercado = registro[2]
                                  )
                        formato = self.bloco_ree['formatoB']

                    conta_ree += 1

                    f.write(formato.format(**row))

                    linha += 1

                f.write(' 999\n')

                if self.bloco_ficticias['flag'] == 1:
                    f.write('                         1')

            print('OK! Escrita do', self.nome_arquivo ,'realizada com sucesso. (', conta_ree,
                  'Reservatórios de Equivalentes de Energia  )')

        except Exception:
            raise

    def get(self, entrada):
        """
        Busca um reservatório equivalente de energia do REE.DAT e retorna um dicionario de dados contendo todas as
        informacoes do REE

        :param entrada: string com o nome do REE ou inteiro/float com o numero de referencia do REE

        """

        posicao = None
        if (type(entrada) == float) or (type(entrada) == int):

            ree_df = self.bloco_ree['df'][self.bloco_ree['df']['codigo'] == entrada]

            tamanho = ree_df.shape
            tamanho = tamanho[0]

            if tamanho == 0:
                return None

        if type(entrada) == str:
            ree_df = self.bloco_ree['df'][(self.bloco_ree['df']['nome'].str.strip()).str.upper() ==
                                          entrada.strip().upper()]

            tamanho = ree_df.shape
            tamanho = tamanho[0]

            if tamanho == 0:
                return None

        registro = ree_df.iloc[0].values

        ree = {
            'codigo': registro[0],
            'nome': registro[1],
            'submercado': registro[2],
            'mes': registro[3],
            'ano': registro[4],
            'earmax': registro[5],
            'ena_bruta': registro[6],
            'ec': registro[7],
            'efio_bruta': registro[8]
        }

        return ree

    def put(self, ree):

        ree_df = self.bloco_ree['df'][self.bloco_ree['df']['codigo'] == ree['codigo']]

        tamanho = ree_df.shape
        tamanho = tamanho[0]

        if tamanho == 0:
            return None

        self.bloco_ree['df'][self.bloco_ree['df']['codigo'] == ree['codigo']] = [ ree['codigo'],
                                                                                  ree['nome'].ljust(10),
                                                                                  ree['submercado'],
                                                                                  ree['mes'],
                                                                                  ree['ano']]

        return

    def _calc_earm_max(self, confhd, codigo_ree):
        nanos = len(confhd._status_vol_morto['valor'][0])
        earmax = np.zeros((nanos, 12), 'f')
        for iusi in confhd.lista_uhes():
            uhe = confhd.get(iusi)
            if uhe['vol_util'] > 0 and uhe['ree'] == codigo_ree:
                for iano in range(nanos):
                    for imes in range(12):
                        if uhe['status_vol_morto'][iano][imes] == 2:
                            earmax[iano][imes] +=  uhe['ro_acum'][iano][imes] * uhe['vol_util'] / 2.63
        return earmax

    def _calc_ena(self, confhd, codigo_ree):

        nanos = len(confhd._status_vol_morto['valor'][0])

        nanos_hist = len(confhd._vazoes['valor'][0])

        ec = np.zeros((nanos, 12, nanos_hist), 'f')
        #efio = np.zeros((nanos, 12, nanos_hist), 'f')
        ena = np.zeros((nanos, 12, nanos_hist), 'f')

        for iusi, ree in enumerate(confhd._ree['valor']):
            if ree == codigo_ree:
                codigo = confhd._codigo['valor'][iusi]
                for iano in range(nanos):
                    for imes in range(12):
                        if confhd._status_vol_morto['valor'][iusi][iano][imes] == 2:
                            if confhd._vol_util['valor'][iusi] > 0:
                                ec[iano][imes] += confhd._ro_acum_med['valor'][iusi][iano][imes] * confhd.vaz_inc_entre_res(codigo, iano, imes)
                            #else:
                            #    efio[iano][imes] += confhd._ro_65['valor'][iusi][iano][imes] * confhd.vaz_inc_entre_res(codigo, iano, imes)
                            for ianoh in range(nanos_hist):
                                ena[iano][imes][ianoh] += confhd._ro_65['valor'][iusi][iano][imes] * confhd._vazoes['valor'][iusi][ianoh][imes]
        efio = ena - ec
        return [ena, ec, efio]
