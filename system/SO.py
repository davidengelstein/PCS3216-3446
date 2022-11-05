import logging
import coloredlogs
import sys
import time
import threading

from .job import Job, JobState, JobPriority
from .event import IOFinishedEvent, KillProcessEvent
from queue import Queue, PriorityQueue, Empty

logger = logging.getLogger(__name__)

class SO:
    def __init__(self, multiprogramming=4):
        self.event_queue = Queue()
        self.jobs_queue = PriorityQueue()
        self.ready_jobs = []
        self.active_jobs = []
        self.waiting_io_jobs = []
        self.running_jobs = 0

        self.processing = threading.Lock()

        self.multiprogramming = multiprogramming
        self.current_cycle = 0

        logger.info(f'Ciclo {self.current_cycle:05d} | Inicializando Job Scheduler')
        logger.info(f'Ciclo {self.current_cycle:05d} | Inicializando Traffic Controller')
        logger.info(f'Ciclo {self.current_cycle:05d} | Inicializando Process Scheduler')

        self.schedulers = threading.Thread(target=self._schedulers)
        self.processor = threading.Thread(target=self._run)

        self.schedulers.start()
        self.processor.start()

    def _event_process(self):
        # while True:
        try:
            event = self.event_queue.get(False)
        except Empty:
            return

        event_name = type(event).__name__

        if type(event) == IOFinishedEvent:
            logger.info(f'Ciclo {self.current_cycle:05d} | SO | Evento de I/O ({event_name}) para o job {event.job_id}.')
            event.process()

            for j in self.waiting_io_jobs[:]:
                if j.id == event.job_id:
                    self.waiting_io_jobs.remove(j)
                    j.state = JobState.READY
                    self.ready_jobs.append(j)
                    return

        if type(event) == KillProcessEvent:
            logger.info(f'Ciclo {self.current_cycle:05d} | SO | Matar job {event.job_id}.')
            event.process()

            for j in self.waiting_io_jobs[:]:
                if j.id == event.job_id:
                    self.waiting_io_jobs.remove(j)
                    j.state = JobState.DONE
                    return

            for j in self.active_jobs[:]:
                if j.id == event.job_id:
                    self.running_jobs -= 1
                    self.active_jobs.remove(j)
                    j.state = JobState.DONE
                    return

            for j in self.ready_jobs[:]:
                if j.id == event.job_id:
                    self.ready_jobs.remove(j)
                    j.state = JobState.DONE
                    return

        logger.warning(f'Ciclo {self.current_cycle:05d} | SO | Evento Desconhecido... {event_name}')

    def _job_scheduler(self):
        try:
            new_job = self.jobs_queue.get(False) 
        except Empty:
            return

        logger.info(f'Ciclo {self.current_cycle:05d} | Job Scheduler | Job {new_job.id} está PRONTO (delay: {self.current_cycle - new_job.arrive_time} ciclos)')
        new_job.state = JobState.READY
        new_job.start_time = self.current_cycle
        self.ready_jobs.append(new_job)  

    def _process_scheduler(self):
        for job in self.ready_jobs[:]:
            if self.running_jobs >= self.multiprogramming:
                continue

            logger.info(f'Ciclo {self.current_cycle:05d} | Process Scheduler | Iniciando job {job.id} (delay: {self.current_cycle - job.arrive_time} ciclos)')
            self.ready_jobs.remove(job)
            job.state = JobState.RUNNING
            self.running_jobs += 1
            self.active_jobs.append(job) # Initilize job with 0 used cycles

    def _traffic_controller(self):
        pass

    def add_job(self, job: Job):
        if job.io[0]:
            logger.info(f'Ciclo {self.current_cycle:05d} | SO | Adicionando job (id {job.id}) com prioridade {job.priority.name} à fila com E/S no ciclo {job.io[1]}|{job.io[2]}.')
        else:
            logger.info(f'Ciclo {self.current_cycle:05d} | SO | Adicionando job (id {job.id}) com prioridade {job.priority.name} à fila.')
        job.state = JobState.WAIT_RESOURCES
        job.arrive_time = self.current_cycle
        self.jobs_queue.put(job)

    def io_finish(self, job_id):
        evt = IOFinishedEvent(job_id)
        self.event_queue.put(evt)

    def _schedulers(self):
        while True:
            self.processing.acquire()
            self._job_scheduler()
            self._process_scheduler()
            self._traffic_controller()
            self._event_process()
            self.processing.release()

    def _run(self):
        while True:
            self.processing.acquire()

            if len(self.active_jobs) == 0:
                self.current_cycle += 1
                self.processing.release()
                time.sleep(0.1)
                continue

            _aj = self.active_jobs.copy()

            for job in self.active_jobs[:]:
                job.cycle()

                if job.io[0] and job.current_cycle == job.io[1]:
                    logger.info(f'Ciclo {self.current_cycle:05d} | SO | Job {job.id} aguardando E/S.')
                    t = threading.Timer(0.1 * job.io[2], self.io_finish, [job.id])
                    job.state = JobState.WAIT_IO

                    self.running_jobs -= 1
                    self.active_jobs.remove(job)
                    self.waiting_io_jobs.append(job)

                    t.start()

                if job.state == JobState.DONE:
                    logger.info(f'Ciclo {self.current_cycle:05d} | SO | Job {job.id} terminado (delay: {self.current_cycle - job.start_time} ciclos).')

                    self.running_jobs -= 1
                    self.active_jobs.remove(job)

                self.current_cycle += 1
                time.sleep(0.1)

            self.processing.release()
            time.sleep(0.01)
