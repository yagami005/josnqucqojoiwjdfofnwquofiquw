import datetime
import requests
import telebot
import time
import json
import csv
import os
import random

class WebScraper:
    
    def __init__(self):
        # Configurações
        self.game = "Blaze Double"
        self.token = '7486302148:AAHORAtaTUzv_z62SnjJEIeNcllrPeRwYiU'
        self.chat_id = '-1002310257460'
        self.url_API = 'https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1'
        self.gales = 2  # Ajustado para 2 gales
        self.protection = True
        self.link = 'blaze-codigo.com/r/WKPQ6'

        # Contadores de resultados
        self.win_results = 0
        self.branco_results = 0
        self.loss_results = 0
        self.max_hate = 0
        self.win_hate = 0
        self.wins_without_gale = 0
        self.wins_martingale_1 = 0
        self.wins_martingale_2 = 0

        # Atributos auxiliares
        self.count = 0
        self.analisar = True
        self.direction_color = 'None'
        self.message_delete = False
        self.bot = telebot.TeleBot(token=self.token, parse_mode='MARKDOWN')
        self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.check_date = self.date_now
        self.current_pattern = None

        # Atributo para armazenar os padrões indicados
        self.report_data = []

        # Arquivos de estratégia
        self.strategy_files = ["estrategy1.csv", "estrategy2.csv"]
        self.current_strategy_file = 0

    def restart(self):
        if self.date_now != self.check_date:
            print('Reiniciando bot!')
            self.check_date = self.date_now
            self.bot.send_sticker(self.chat_id, sticker='CAACAgEAAxkBAAEBbJJjXNcB92-_4vp2v0B3Plp9FONrDwACvgEAAsFWwUVjxQN4wmmSBCoE')
            self.results()

            # Zera os resultados
            self.win_results = 0
            self.loss_results = 0
            self.branco_results = 0
            self.wins_without_gale = 0
            self.wins_martingale_1 = 0
            self.wins_martingale_2 = 0
            self.max_hate = 0
            self.win_hate = 0
            time.sleep(10)

            self.bot.send_sticker(self.chat_id, sticker='CAACAgEAAxkBAAEBPQZi-ziImRgbjqbDkPduogMKzv0zFgACbAQAAl4ByUUIjW-sdJsr6CkE')
            self.results()
            return True
        else:
            return False

    def results(self):
        if self.win_results + self.branco_results + self.loss_results != 0:
            a = 100 / (self.win_results + self.branco_results + self.loss_results) * (self.win_results + self.branco_results)
        else:
            a = 0
        self.win_hate = (f'{a:,.2f}%')

        self.bot.send_message(chat_id=self.chat_id, text=(f'''
► PLACAR GERAL = ✅{self.win_results} | ⚪️{self.branco_results} | 🚫{self.loss_results}
► WINS: 
   - Sem Gale: {self.wins_without_gale}
   - Gale 1: {self.wins_martingale_1}
   - Gale 2: {self.wins_martingale_2}
► Consecutivas = {self.max_hate}
► Assertividade = {self.win_hate}
'''))
        return

    def alert_sinal(self):
        message_id = self.bot.send_message(self.chat_id, text='''⚠️ ANALISANDO, FIQUE ATENTO!!!''').message_id
        self.message_ids = message_id
        self.message_delete = True
        return

    def alert_gale(self):
        if self.count <= self.gales:
            gale_number = self.count
            gale_message = f'⚠️ Vamos para o {gale_number}ª GALE'
        else:
            gale_number = self.count - self.gales
            gale_message = f'⚠️ Vamos para o {gale_number}ª GALE EXTRA'
        self.message_ids = self.bot.send_message(self.chat_id, text=gale_message).message_id
        self.message_delete = True
        return

    def delete(self):
        if self.message_delete == True:
            try:
                self.bot.delete_message(chat_id=self.chat_id, message_id=self.message_ids)
            except telebot.apihelper.ApiException as e:
                print(f"Error deleting message: {e}")
            self.message_delete = False

    def get_last_pattern_result(self, pattern):
        """Retorna o último resultado (WIN/LOSS/BRANCO) para o padrão especificado no dia atual"""
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        try:
            with open('report_history.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reversed(list(reader)):
                    if row['Padrao'] == ''.join(pattern) and row['Data'] == today:
                        return row['Resultado']
        except FileNotFoundError:
            pass
        return "N/A"

    def calculate_average_wins(self, pattern):
        """Calcula a média de wins consecutivos para o padrão no dia atual"""
        pattern_str = ''.join(pattern)
        win_streaks = []
        current_streak = 0
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        
        try:
            with open('report_history.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Padrao'] == pattern_str and row['Data'] == today:
                        if row['Resultado'] in ['WIN', 'BRANCO']:
                            current_streak += 1
                        else:
                            if current_streak > 0:
                                win_streaks.append(current_streak)
                            current_streak = 0
                if current_streak > 0:  # Adiciona a sequência atual se terminou em WIN/BRANCO
                    win_streaks.append(current_streak)
        except FileNotFoundError:
            pass
        
        return round(sum(win_streaks)/len(win_streaks), 1) if win_streaks else 0

    def get_pattern_count_today(self, pattern):
        """Conta quantas vezes o padrão apareceu hoje"""
        pattern_str = ''.join(pattern)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        count = 0
        
        try:
            with open('report_history.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Padrao'] == pattern_str and row['Data'].startswith(today):
                        count += 1
        except FileNotFoundError:
            pass
        
        return count

    def save_to_history(self, pattern, result):
        """Salva cada entrada no histórico completo"""
        headers = ['Data', 'Hora', 'Padrao', 'Resultado', 'Estagio']
        data = {
            'Data': datetime.datetime.now().strftime("%d/%m/%Y"),
            'Hora': datetime.datetime.now().strftime("%H:%M:%S"),
            'Padrao': ''.join(pattern),
            'Resultado': result,
            'Estagio': f'Martingale {self.count}' if self.count <= self.gales else f'Gale {self.count - self.gales}'
        }
        
        file_exists = os.path.isfile('report_history.csv')
        
        with open('report_history.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

    def get_last_number(self):
        """Obtém o último número da API"""
        try:
            response = requests.get(self.url_API, timeout=10)
            json_data = json.loads(response.text)
            if json_data and isinstance(json_data, list) and 'roll' in json_data[0]:
                return json_data[0]['roll']
        except Exception as e:
            print(f"Erro ao obter último número: {e}")
        return None

    def get_pattern_stats(self, padrao):
        file_path = "report.csv"
        pattern_str = ''.join(padrao)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row['Padrao'] == pattern_str:
                        return {
                            "Martingale 0": row["Martingale 0"],
                            "Martingale 1": row["Martingale 1"],
                            "Martingale 2": row["Martingale 2"],
                            "Branco 0": row["Branco 0"],
                            "Branco 1": row["Branco 1"],
                            "Branco 2": row["Branco 2"],
                            "Loss": row["Loss"]
                        }
        return None


    def send_sinal(self, padrao):
        print("Sinal enviado, aguardando resultado...")
        self.current_pattern = padrao
        emotes = {'V': '🔴', 'P': '⚫️', 'B': '⚪️'}
        padrao_emotes = ''.join(emotes.get(char, char) for char in padrao)
        self.analisar = False
        
        pattern_stats = self.get_pattern_stats(padrao)
        last_number = self.get_last_number()
        count_today = self.get_pattern_count_today(padrao)
        ultimo_resultado = self.get_last_pattern_result(padrao)
        media_wins = self.calculate_average_wins(padrao)
        
        pattern_str = ''.join(padrao)
        today = datetime.datetime.now().strftime("%d/%m/%Y")
        wins_sem_gale = 0
        wins_gale1 = 0
        wins_gale2 = 0
        brancos = 0
        losses = 0
        
        # Contagem ajustada para todas as aparições do padrão no dia
        try:
            with open('report_history.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Padrao'] == pattern_str and row['Data'] == today:
                        if row['Resultado'] == 'WIN':
                            if row['Estagio'] == 'Martingale 0':
                                wins_sem_gale += 1
                            elif row['Estagio'] == 'Martingale 1':
                                wins_gale1 += 1
                            elif row['Estagio'] == 'Martingale 2':
                                wins_gale2 += 1
                        elif row['Resultado'] == 'BRANCO':
                            brancos += 1
                        elif row['Resultado'] == 'LOSS':
                            losses += 1
        except FileNotFoundError:
            pass
        
        total_today = wins_sem_gale + wins_gale1 + wins_gale2 + brancos + losses
        prob_win_today = ((wins_sem_gale + wins_gale1 + wins_gale2 + brancos) / total_today * 100) if total_today > 0 else 0
        
        if pattern_stats:
            try:
                total_wins = int(pattern_stats["Martingale 0"]) + int(pattern_stats["Martingale 1"]) + int(pattern_stats["Martingale 2"])
                total_brancos = int(pattern_stats["Branco 0"]) + int(pattern_stats["Branco 1"]) + int(pattern_stats["Branco 2"])
                total_losses = int(pattern_stats["Loss"])
                total_tries = total_wins + total_brancos + total_losses
                
                win_rate = (total_wins / total_tries * 100) if total_tries > 0 else 0
                branco_rate = (total_brancos / total_tries * 100) if total_tries > 0 else 0
                loss_rate = (total_losses / total_tries * 100) if total_tries > 0 else 0
                win_plus_branco_rate = ((total_wins + total_brancos) / total_tries * 100) if total_tries > 0 else 0
                
                # Dicas estratégicas (mantive as profissionais da versão anterior)
                dicas = []
                if ultimo_resultado == "LOSS":
                    loss_tips = [
                        "⏳ Último resultado foi LOSS - Analise com cautela.",
                        "⏳ O padrão registrou LOSS recentemente - Observe o histórico.",
                        "⏳ Última tentativa resultou em LOSS - Avalie o momento.",
                        "⏳ LOSS anterior no padrão - Considere os riscos.",
                        "⏳ Última entrada terminou em LOSS - Verifique o contexto.",
                        "⏳ Padrão com LOSS recente - Prossiga com atenção.",
                        "⏳ O último resultado foi LOSS - Examine o cenário.",
                        "⏳ LOSS detectado na última tentativa - Tenha cuidado.",
                        "⏳ Última ocorrência foi LOSS - Avalie o próximo passo.",
                        "⏳ Registro de LOSS anterior - Considere a tendência.",
                        "⏳ Última chamada deu LOSS - Observe os detalhes.",
                        "⏳ Padrão com falha recente - Analise antes de agir.",
                        "⏳ LOSS na última entrada - Verifique a Tendência atual.",
                        "⏳ Resultado anterior foi LOSS - Prossiga com prudência.",
                        "⏳ Último padrão terminou em LOSS - Atenção ao timing.",
                        "⏳ LOSS recente no histórico - Avalie o risco envolvido.",
                        "⏳ Última tentativa falhou - Considere os indicadores.",
                        "⏳ Padrão com LOSS prévio - Observe o desempenho.",
                        "⏳ LOSS registrado anteriormente - Analise o padrão.",
                        "⏳ Última entrada foi LOSS - Verifique os sinais."
                    ]
                    dicas.append(random.choice(loss_tips))
                
                if win_rate >= 89:
                    hot_tips = [
                        f"🔥 Taxa de acerto em {win_rate:.0f}% - Histórico elevado.",
                        f"🔥 Padrão com {win_rate:.0f}% de sucesso - Desempenho consistente.",
                        f"🔥 {win_rate:.0f}% Chance maior de Vitória.",
                        f"🔥 Alta performance com {win_rate:.0f}% - Observe a tendência.",
                        f"🔥 {win_rate:.0f}% de acerto no histórico - Taxa significativa.",
                        f"🔥 Padrão registra {win_rate:.0f}% - chance de vitória mais elevada",
                        f"🔥 {win_rate:.0f}% de sucesso até agora - Histórico favorável.",
                        f"🔥 Taxa elevada de {win_rate:.0f}% - Avalie a tendência.",
                        f"🔥 {win_rate:.0f}% no padrão - Desempenho acima da média.",
                        f"🔥 Histórico com {win_rate:.0f}% de acerto maior chance de vitória.",
                        f"🔥 {win_rate:.0f}% de vitórias - Taxa expressiva.",
                        f"🔥 Padrão em {win_rate:.0f}% - Resultados consistentes.",
                        f"🔥 Taxa de {win_rate:.0f}% acumulada - Observe a tendência.",
                        f"🔥 {win_rate:.0f}% de acerto registrado - Tendência favoravel.",
                        f"🔥 Padrão com {win_rate:.0f}% - Histórico positivo.",
                        f"🔥 {win_rate:.0f}% de sucesso padrão quente.",
                        f"🔥 Taxa de vitórias em {win_rate:.0f}% - avalie a tendência.",
                        f"🔥 {win_rate:.0f}% no histórico - Taxa alta registrada.",
                        f"🔥 Padrão com {win_rate:.0f}% de acerto",
                        f"🔥 {win_rate:.0f}% de vitórias acumuladas."
                    ]
                    dicas.append(random.choice(hot_tips))
                elif win_rate <= 81:
                    risk_tips = [
                        f"⚠️ Taxa de {win_rate:.0f}% - Desempenho abaixo da média.",
                        f"⚠️ Apenas {win_rate:.0f}% de acerto - Considere os riscos.",
                        f"⚠️ Padrão com {win_rate:.0f}% - Histórico instável.",
                        f"⚠️ {win_rate:.0f}% de vitórias - Avalie com cautela.",
                        f"⚠️ Taxa baixa de {win_rate:.0f}%.",
                        f"⚠️ {win_rate:.0f}% no padrão - Desempenho limitado.",
                        f"⚠️ Histórico com {win_rate:.0f}% - Observe a tendência.",
                        f"⚠️ {win_rate:.0f}% de acerto - Risco elevado presente.",
                        f"⚠️ Taxa de {win_rate:.0f}% acumulada - Analise a tendência.",
                        f"⚠️ Padrão em {win_rate:.0f}% - Resultados inconsistentes.",
                        f"⚠️ {win_rate:.0f}% de sucesso - Considere o histórico.",
                        f"⚠️ Taxa de vitórias em {win_rate:.0f}% - Cuidado necessário.",
                        f"⚠️ {win_rate:.0f}% no histórico - Desempenho fraco.",
                        f"⚠️ Padrão com {win_rate:.0f}% - risco alto.",
                        f"⚠️ {win_rate:.0f}% de acerto - Risco a ser considerado.",
                        f"⚠️ Taxa baixa em {win_rate:.0f}% - Veja a Tendência atual.",
                        f"⚠️ {win_rate:.0f}% de vitórias - Analise antes de prosseguir.",
                        f"⚠️ Histórico de {win_rate:.0f}% - Observe com atenção.",
                        f"⚠️ Padrão registra {win_rate:.0f}% - Taxa reduzida.",
                        f"⚠️ {win_rate:.0f}% acumulado - Considere a tendência."
                    ]
                    dicas.append(random.choice(risk_tips))
                else:
                    moderate_tips = [
                        f"🟡 Taxa de {win_rate:.0f}% - Desempenho equilibrado.",
                        f"🟡 Padrão com {win_rate:.0f}% - Analise o histórico.",
                        f"🟡 {win_rate:.0f}% de acerto - Considere a tendência.",
                        f"🟡 Taxa média de {win_rate:.0f}% - Risco moderado.",
                        f"🟡 {win_rate:.0f}% no padrão - Avalie os resultados anteriores.",
                        f"🟡 Histórico em {win_rate:.0f}% - Observe analise os statusdo dia.",
                        f"🟡 {win_rate:.0f}% de vitórias - Desempenho estável.",
                        f"🟡 Taxa de {win_rate:.0f}% acumulada - Considere a tendência.",
                        f"🟡 Padrão registra {win_rate:.0f}% - Veja a tendência.",
                        f"🟡 {win_rate:.0f}% de sucesso - Analise o cenário.",
                        f"🟡 Taxa moderada de {win_rate:.0f}% - Observe o comportamento do padrão.",
                        f"🟡 {win_rate:.0f}% no histórico - Considere os indicadores.",
                        f"🟡 Padrão com {win_rate:.0f}% - Avalie o desempenho atual do padrão.",
                        f"🟡 {win_rate:.0f}% de acerto - risco moderado.",
                        f"🟡 Taxa de vitórias em {win_rate:.0f}% - Analise com atenção.",
                        f"🟡 {win_rate:.0f}% acumulado - Observe o comportamento do padrão no dia.",
                        f"🟡 Padrão em {win_rate:.0f}% - Considere a tendência atual.",
                        f"🟡 Taxa de {win_rate:.0f}% - risco moderado.",
                        f"🟡 {win_rate:.0f}% de sucesso - Veja o histórico recente.",
                        f"🟡 {win_rate:.0f}% no padrão - Analise a tendência."
                    ]
                    dicas.append(random.choice(moderate_tips))
                
                if branco_rate >= 16:
                    branco_tips = [
                        f"⚪️ Taxa de branco em {branco_rate:.0f}% - Considere o histórico.",
                        f"⚪️ {branco_rate:.0f}% de incidência de branco - Avalie o risco.",
                        f"⚪️ Branco registra {branco_rate:.0f}% - Observe o padrão.",
                        f"⚪️ Alta taxa de {branco_rate:.0f}% em branco - Veja os dados.",
                        f"⚪️ {branco_rate:.0f}% de branco no histórico - Analise a Tendência.",
                        f"⚪️ Padrão com {branco_rate:.0f}% de branco - Considere os números.",
                        f"⚪️ Taxa elevada de {branco_rate:.0f}% - Observe os indicadores.",
                        f"⚪️ {branco_rate:.0f}% de branco acumulado - Avalie o cenário.",
                        f"⚪️ Branco em {branco_rate:.0f}% - Veja o desempenho.",
                        f"⚪️ {branco_rate:.0f}% de incidência - Considere a tendência.",
                        f"⚪️ Taxa de {branco_rate:.0f}% em branco - Analise os sinais.",
                        f"⚪️ Padrão registra {branco_rate:.0f}% - Observe com atenção.",
                        f"⚪️ {branco_rate:.0f}% de branco - Avalie o contexto.",
                        f"⚪️ Alta presença de {branco_rate:.0f}% - Veja o histórico.",
                        f"⚪️ {branco_rate:.0f}% em branco - Considere a Tendência atual.",
                        f"⚪️ Taxa de branco com {branco_rate:.0f}% - Analise o padrão.",
                        f"⚪️ {branco_rate:.0f}% de incidência - Observe o comportamento.",
                        f"⚪️ Branco acumula {branco_rate:.0f}% - Avalie os resultados.",
                        f"⚪️ Padrão com {branco_rate:.0f}% em branco - Veja os números.",
                        f"⚪️ {branco_rate:.0f}% de branco registrado - Considere os dados."
                    ]
                    dicas.append(random.choice(branco_tips))
                
                if media_wins >= 2:
                    streak_tips = [
                        f"📈 {media_wins} vitórias consecutivas - Analise o histórico.",
                        f"📈 Padrão com {media_wins} acertos seguidos - Veja a Tendência.",
                        f"📈 {media_wins} wins em sequência - Considere o desempenho.",
                        f"📈 Sequência de {media_wins} vitórias - Observe os dados.",
                        f"📈 {media_wins} acertos consecutivos - Avalie a tendência.",
                        f"📈 Padrão registra {media_wins} wins seguidos - Veja o comportamento do padrão.",
                        f"📈 {media_wins} vitórias em fila - Analise o comportamento do padrão.",
                        f"📈 Sequência com {media_wins} acertos - Considere a tendência.",
                        f"📈 {media_wins} wins consecutivos - Observe o padrão.",
                        f"📈 Taxa de {media_wins} vitórias seguidas - Avalie o timing.",
                        f"📈 {media_wins} acertos em sequência - Veja o desempenho.",
                        f"📈 Padrão em {media_wins} wins seguidos - Analise os sinais.",
                        f"📈 {media_wins} vitórias acumuladas - Considere a Tendência atual.",
                        f"📈 Sequência de {media_wins} acertos - Observe os indicadores.",
                        f"📈 {media_wins} wins em fila - Avalie o histórico recente.",
                        f"📈 Padrão com {media_wins} vitórias - Veja o comportamento.",
                        f"📈 {media_wins} acertos consecutivos - Considere os resultados.",
                        f"📈 Sequência registra {media_wins} wins - Analise o padrão.",
                        f"📈 {media_wins} vitórias seguidas - Observe o cenário atual.",
                        f"📈 {media_wins} wins consecutivos - Avalie os dados."
                    ]
                    dicas.append(random.choice(streak_tips))
                
                dicas_str = "\n".join(dicas) if dicas else "💡 Sem dados suficientes - Analise o padrão."
            
                mensagem = f"""
┌── 🎯 *ENTRADA CONFIRMADA* ──┐  
│ *Padrão:* {padrao_emotes}  
│ *Apareceu {count_today} vezes hoje*  
├───────────────  
│ *Apostar:* {self.direction_color}  
│ ⏳ *Entrar Após o Nº:* {last_number if last_number else 'N/A'}  
│ ⚪️ *Proteger:* Branco  
│ 🔄 *Até:* 2 Gales  
├─ 📊 *DESEMPENHO ATÉ (G2)* ──  
│  
│ ✅ Resultados verificados: {total_tries}  
│ ✅ {total_wins} Wins na Cor ({win_rate:.0f}%)  
│ ⚪️ {total_brancos} Brancos ({branco_rate:.0f}%)  
│ ✅ Wins Cor + Branco: ({win_plus_branco_rate:.0f}%)  
│ 💀 {total_losses} Loss ({loss_rate:.0f}%)  
│  
├─ 📈 *STATUS HOJE* ──  
│  
│ ✅ *Sem Gale:* {wins_sem_gale}  
│ ✅ *Gale 1:* {wins_gale1}  
│ ✅ *Gale 2:* {wins_gale2}  
│ ⚪️ *Branco:* {brancos}  
│ 🚫 *Loss:* {losses}  
│ 📊 *Prob. Total de WIN Hoje:* {prob_win_today:.0f}%  
│  
├─ 📝 *STATUS DO PADRÃO* ──  
│ {dicas_str}  
└── 🔗 [Blaze]({self.link}) ──┘  
            """
            except (KeyError, ValueError) as e:
                print(f"Erro ao processar estatísticas do padrão: {e}")
                mensagem = f"""
┌── 🎯 *ENTRADA CONFIRMADA* ──┐  
│ *Padrão:* {padrao_emotes}  
│ *Status:* Novo  
├───────────────  
│ *Apostar:* {self.direction_color}  
│ ⏳ *Entrar Após o Nº:* {last_number if last_number else 'N/A'}  
│ ⚪️ *Proteger:* Branco  
│ 🔄 *Até:* 2 Gales  
├─ 📝 *DICA* ──  
│ 💡 Padrão novo - Analise com cautela.
└── 🔗 [Blaze]({self.link}) ──┘  
            """
        else:
            mensagem = f"""
┌── 🎯 *ENTRADA CONFIRMADA* ──┐  
│ *Padrão:* {padrao_emotes}  
│ *Status:* Novo  
├───────────────  
│ *Apostar:* {self.direction_color}  
│ ⏳ *Entrar Após o Nº:* {last_number if last_number else 'N/A'}  
│ ⚪️ *Proteger:* Branco  
│ 🔄 *Até:* 2 Gales  
├─ 📝 *DICA* ──  
│ 💡 Padrão novo - Analise com cautela.
└── 🔗 [Blaze]({self.link}) ──┘  
        """
    
        try:
            self.bot.send_message(chat_id=self.chat_id, text=mensagem, parse_mode='MARKDOWN')
        except telebot.apihelper.ApiException as e:
            print(f"Erro ao enviar mensagem para o Telegram: {e}")
            self.bot.send_message(chat_id=self.chat_id, text=mensagem, parse_mode=None)
        
        current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.report_data.append({
            "Data e Hora": current_time,
            "Padrao": ''.join(padrao),
            "Estagio": "Entrada Normal",
            "Resultado": "Pending"
        })
        
        self.generate_report()
        print("Relatório gerado com sucesso!")
        return

    def martingale(self, result):
        if result == "WIN":
            print(f"WIN")
            self.win_results += 1
            self.max_hate += 1
            self.save_to_history(self.current_pattern, "WIN")
    
            if self.count == 0:
                win_message = "✅✅✅ WIN SEM GALE ✅✅✅"
                self.wins_without_gale += 1
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 0"
                    self.report_data[-1]["Resultado"] = "WIN"
            elif self.count == 1:
                win_message = "✅✅✅ WIN NO G1 ✅✅✅"
                self.wins_martingale_1 += 1
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 1"
                    self.report_data[-1]["Resultado"] = "WIN"
            elif self.count == 2:
                win_message = "✅✅✅ WIN NO G2 ✅✅✅"
                self.wins_martingale_2 += 1
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 2"
                    self.report_data[-1]["Resultado"] = "WIN"
    
            self.bot.send_message(chat_id=self.chat_id, text=win_message)
    
        elif result == "LOSS":
            self.count += 1
            self.save_to_history(self.current_pattern, "LOSS")
            gale_win = False
    
            if self.count > self.gales:
                if not gale_win:
                    print(f"LOSS")
                    self.loss_results += 1
                    self.max_hate = 0
                    self.bot.send_message(chat_id=self.chat_id, text=(f'''🚫🚫🚫 LOSS 🚫🚫🚫'''))
                    self.current_strategy_file = 1 - self.current_strategy_file
                    print("Alternando estratégias após LOSS")
                    if self.report_data:
                        self.report_data[-1]["Resultado"] = "LOSS"
            else:
                print(f"Vamos para o {self.count}ª gale!")
                self.alert_gale()
                return
    
        elif result == "BRANCO":
            print(f"BRANCO")
            self.branco_results += 1
            self.max_hate += 1
            self.save_to_history(self.current_pattern, "BRANCO")
    
            if self.count == 0:
                branco_message = "✅✅✅ BRANCO SEM GALE ✅✅✅"
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 0"
                    self.report_data[-1]["Resultado"] = "BRANCO"
            elif self.count == 1:
                branco_message = "✅✅✅ BRANCO G1 ✅✅✅"
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 1"
                    self.report_data[-1]["Resultado"] = "BRANCO"
            elif self.count == 2:
                branco_message = "✅✅✅ BRANCO G2 ✅✅✅"
                if self.report_data:
                    self.report_data[-1]["Estagio"] = "Martingale 2"
                    self.report_data[-1]["Resultado"] = "BRANCO"
    
            self.bot.send_message(chat_id=self.chat_id, text=branco_message)
    
        self.generate_report()
        print("Relatório gerado com sucesso!")
    
        self.count = 0
        self.analisar = True
        self.results()
        self.restart()
    
        if result == "LOSS":
            self.estrategy([])

    def check_results(self, recent_result):
        if recent_result == 'V' and self.direction_color == '🔴':
            self.martingale('WIN')
        elif recent_result == 'V' and self.direction_color == '⚫️':
            self.martingale('LOSS')
        elif recent_result == 'P' and self.direction_color == '⚫️':
            self.martingale('WIN')
        elif recent_result == 'P' and self.direction_color == '🔴':
            self.martingale('LOSS')
        elif recent_result == 'B':
            self.martingale('BRANCO')
        elif recent_result.startswith('G'):
            self.martingale(recent_result)

    def processar_resultado(self, resultado_final):
        for entrada in self.report_data:
            if entrada['Resultado'] == 'Pending':
                entrada['Resultado'] = resultado_final
        self.generate_report()

    def generate_report(self):
        file_path = "report.csv"
        
        existing_data = {}
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_data[row['Padrao']] = {
                        'Martingale 0': int(row['Martingale 0']),
                        'Martingale 1': int(row['Martingale 1']),
                        'Martingale 2': int(row['Martingale 2']),
                        'Branco 0': int(row['Branco 0']),
                        'Branco 1': int(row['Branco 1']),
                        'Branco 2': int(row['Branco 2']),
                        'Loss': int(row['Loss'])
                    }
        except FileNotFoundError:
            print(f"Arquivo {file_path} não encontrado. Criando um novo...")
        
        for entry in self.report_data:
            pattern = entry['Padrao']
            resultado = entry['Resultado']
            estagio = entry['Estagio']
            
            if pattern not in existing_data:
                existing_data[pattern] = {
                    'Martingale 0': 0, 'Martingale 1': 0, 'Martingale 2': 0,
                    'Branco 0': 0, 'Branco 1': 0, 'Branco 2': 0, 'Loss': 0
                }
            
            if resultado in ['WIN', 'LOSS', 'BRANCO']:
                if resultado == 'WIN':
                    existing_data[pattern][estagio] += 1
                elif resultado == 'BRANCO':
                    branco_key = f"Branco {estagio[-1]}"
                    existing_data[pattern][branco_key] += 1
                elif resultado == 'LOSS':
                    existing_data[pattern]['Loss'] += 1
        
        headers = ['Padrao', 'Martingale 0', 'Martingale 1', 'Martingale 2', 
                'Branco 0', 'Branco 1', 'Branco 2', 'Loss']
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for pattern, stats in existing_data.items():
                    row = {'Padrao': pattern}
                    row.update(stats)
                    writer.writerow(row)
            
            print(f"✅ CSV atualizado corretamente! Padrões salvos: {len(existing_data)}")
        
        except Exception as e:
            print(f"❌ Erro ao salvar CSV: {e}")
        
        self.report_data = [entry for entry in self.report_data if entry['Resultado'] == 'Pending']

    def estrategy(self, results):
        finalcor = []
    
        for i in results:
            if i >= 1 and i <= 7: 
                finalcor.append('V')
            elif i >= 8 and i <= 14: 
                finalcor.append('P')
            else:
                finalcor.append('B')
    
        if not self.analisar:
            self.check_results(finalcor[0])
            return
    
        with open(self.strategy_files[self.current_strategy_file], newline='') as f:
            reader = csv.reader(f)
    
            ESTRATEGIAS = []
            for row in reader:
                string = str(row[0])
                split_string = string.split('=')
                values = list(split_string[0])
                dictionary = {'PADRAO': values, 'ENTRADA': split_string[1]}
                ESTRATEGIAS.append(dictionary)
    
            padrao_detectado = False
    
            for i in ESTRATEGIAS:
                detected_pattern = finalcor[:len(i['PADRAO'])][::-1]
                if detected_pattern == i['PADRAO']:
                    print("Padrão detectado. Enviando sinal.")
                    padrao_detectado = True
                    if i['ENTRADA'] == 'P':
                        self.direction_color = '⚫️'
                    elif i['ENTRADA'] == 'V':
                        self.direction_color = '🔴'
                    elif i['ENTRADA'] == 'B':
                        self.direction_color = '⚪️'
                    self.send_sinal(detected_pattern)
                    break
    
            if not padrao_detectado and 'LOSS' in results:
                self.current_strategy_file = 1 - self.current_strategy_file
                print("Alternando estratégias após LOSS")

    def start(self):
        self.generate_report()
        print("Relatório gerado com sucesso!")
        check = []
        while True:
            try:
                self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))

                results = []
                time.sleep(5)

                response = requests.get(self.url_API, timeout=10)
                json_data = json.loads(response.text)
                
                for i in json_data:
                    results.append(i['roll'])

                if check != results:
                    check = results
                    self.delete()
                    self.estrategy(results)

            except Exception as e:
                print(f"Caught an error: {e}")
                continue

# Inicialização
scraper = WebScraper()
scraper.start()