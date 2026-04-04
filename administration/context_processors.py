from .models import Parametre, EntrepriseCliente
from .utils import get_param_value
from .utils import get_societe_context_data


def parametres_societe(request):
    return get_societe_context_data()